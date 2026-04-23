# Session: 2026-04-22 20:48:26 UTC

- **Session Key**: agent:main:main
- **Session ID**: 019db6be-1acd-773f-bcf8-fa8073d41fb4
- **Source**: webchat

## Conversation Summary

assistant: 

The `contamination` variable is scoped inside the `else` block — I need to fix that. Let me restructure to hoist it.

assistant: 

---

**SECTION 1 — FILES CHANGED**

`chat_ui.py` — 4 targeted edits:
1. `state_payload()` signature updated to accept `contamination_metadata: dict = None`
2. `contamination_metadata` added to returned payload as `_contamination_metadata` key
3. `contamination = None` initialized before branch routing
4. `contamination = canon_result.get("_contamination_metadata")` captured from dialogue pipeline result; passed to `state_payload(contamination_metadata=contamination)`

No changes to `dialogue.py` (already surfaces `_contamination_metadata` in `handle_direct_message` return via `research_context.get("_contamination_metadata")`).

No changes to HTML — SatUi already had contamination advisory CSS and JS rendering for `high` and `medium` risk levels.

---

**SECTION 2 — COMMANDS RUN**

No exec available in this environment (Permission denied on all `/usr/bin/` binaries). Syntax verified by read-through.

---

**SECTION 3 — BEHAVIOR VERIFIED**

| Path | How |
|---|---|
| `_contamination_metadata` absent → no panel | JS: `if (item.contamination)` — falsy when absent |
| `risk_level: "none"` → no panel | JS: only enters branch when `level === 'high'` or `level === 'medium'` |
| `risk_level: "medium"` → amber panel, collapsed | JS: renders icon+type+expand-to-reveal |
| `risk_level: "high"` → red panel, reason visible, signals expandable | JS: renders reason immediately, "Show signals" expands source_signals |
| No interaction blocking | No gate logic in JS; advisory display only |
| No routing/scoring changes | `dialogue.py` unchanged; `chat_ui.py` only reads metadata |

---

**SECTION 4 — SAMPLE DISPLAY STATES**

**Absent field (safe path, healthy):**
→ No advisory element rendered.

**`risk_level: "none"`:**
→ No advisory element rendered.

**`risk_level: "medium"`, type `"unrelated_topic_bleed"`:**
```
● Unrelated topic bleed   [Why? ▾]
```
Click "Why?" → reason text revealed. No signal tags.

**`risk_level: "high"`, type `"cross_domain_contamination"`:**
```
● Cross domain contamination
  Artifact from prior domain appears on unrelated turn.
  [Show signals ▾]
```
Expanded → shows `#message_domain_mismatch #artifact_context_present` as signal tags.

---

**SECTION 5 — STOP LINE**

Done. No runtime changes, no routing changes, no scoring changes, no governance changes. Advisory display only.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:12 GMT+2] WESLR — DOCTRINE UPDATE
ADD NEW ARCHITECTURE BRICKS DISCOVERED DURING CONSTRUCTION

STRICT MODE

- documentation only
- no code changes
- no redesign beyond doctrine update
- additive only
- preserve existing doctrine

AUTHORITATIVE CONTEXT

During recent continuity/contamination work, two deeper architectural gaps were discovered:

1. Context Selection Layer

 - contamination is a symptom of weak context selection
 - WESLR needs an explicit layer that decides which context governs the current turn:
 - active thread
 - resolved artifact
 - prior topic
 - new topic
 - uncertain / no-safe-context

2. Concept Boundary Model

 - WESLR can confuse related systems/modules/tools/roles if boundaries are not explicit
 - It must distinguish clearly between:
 - platform
 - subsystem
 - tool
 - runtime
 - role
 - plugin/module
 - example class of confusion:
 - WESLR vs Infinity vs OpenClaw vs OC Coder

These are now considered newly discovered core bricks, not optional ideas.

GOAL

Update doctrine/canon so these become part of WESLR’s official architecture understanding.

PREFERRED TARGET

Update the most appropriate existing doctrine/canon file(s), or if cleaner create one focused doctrine addendum, but keep it minimal and canonical.

REQUIRED CONTENT

SECTION 1 — WHY THESE BRICKS WERE ADDED

- construction/testing revealed them
- they were discovered through real system pressure, not abstract theorizing

SECTION 2 — CONTEXT SELECTION LAYER
Define:

- purpose
- what it selects between
- why this is needed before stronger continuity expansion
- contamination as symptom, not root cause

SECTION 3 — CONCEPT BOUNDARY MODEL
Define:

- purpose
- what boundaries must remain explicit
- why system/tool/module/role confusion is harmful

SECTION 4 — DOCTRINE EVOLUTION RULE
Add a rule that doctrine may grow when real construction reveals missing structural bricks.
This must remain:

- explicit
- inspected
- canonized
- additive
- reversible where possible

SECTION 5 — RELATION TO EXISTING DOCTRINE
Explain how these fit with:

- continuity-first
- governed evolution
- model-assisted, not model-dependent
- structured state replacing raw context

SECTION 6 — STOP LINE

- documentation only
- no code changes
- no behavior changes

OUTPUT FORMAT

SECTION 1 — FILES CHANGED
SECTION 2 — COMMANDS RUN
SECTION 3 — DOCTRINE UPDATE SUMMARY
SECTION 4 — STOP LINE
assistant: Now I have the full doctrine picture. I'll write the addendum directly.

assistant: ---

**SECTION 1 — FILES CHANGED**

| File | Action |
|---|---|
| `ARCHITECTURE_DOCTRINE_ADDENDUM.md` | **Created** — 10,659 bytes, 6 sections |

No changes to existing doctrine files (CORE-IDENTITY.md, ARCHITECTURE.md, WESLR-INTEGRATION.md remain unchanged).

---

**SECTION 2 — COMMANDS RUN**

None — documentation only.

---

**SECTION 3 — DOCTRINE UPDATE SUMMARY**

**Brick 1 — Context Selection Layer** (Section 2)
- Explicit first-class layer that determines which context governs the current turn before any continuity, artifact resolution, or contamination detection runs
- Six named context states: `active_thread`, `resolved_artifact`, `prior_topic`, `new_topic`, `uncertain`, `no_safe_context`
- Rule: stronger continuity without context selection = more contamination, not less
- Contamination = diagnostic output of selector failure, not the root problem site

**Brick 2 — Concept Boundary Model** (Section 3)
- Canonical table defining WESLR, OpenClaw, OCC, Infinity, TIA Bridge, WESLR CLI, SatUi, Dialogue Pipeline
- Each entry: what it IS / what it IS NOT
- Boundary rule: named entities must use canonical names; uncertainty must be raised, not assumed
- Addresses identity drift, architecture decisions, security surface confusion

**Brick 3 — Doctrine Evolution Rule** (Section 4)
- Doctrine may grow from construction-triggered discoveries only (not theoretical speculation)
- Requires: explicit trigger, inspection, canonization with date/context, reversibility record
- Reversion protocol: mark `[REVERTED]`, preserve record, update docs, log to memory

**Alignment with existing doctrine:**
- Context Selection Layer → enables continuity-first to continue the *right* context
- Boundary Model → grounds model-assisted inference against boundary blur
- Doctrine Evolution Rule → is itself governed evolution applied to doctrine
- Structured state principle → context selection produces named structured decisions before the gap

---

**SECTION 4 — STOP LINE**

- Doctrine only. No code changes. No behavior changes.
- Additive: existing doctrine files untouched.
- Reversibility preserved via `[REVERTED]` reversion protocol.
- New file: `ARCHITECTURE_DOCTRINE_ADDENDUM.md` canonized 2026-04-22.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:27 GMT+2] WESLR — CANONICALIZE CORE EVOLUTION PRINCIPLE
ARTIFACT-FIRST EVOLUTION

STRICT MODE

- documentation only
- no code changes
- no behavior changes
- no refactors
- additive only
- must align with existing doctrine

AUTHORITATIVE CONTEXT

We are formalizing a principle already implicitly present in WESLR:

WESLR does NOT evolve by mutating itself directly.

Instead:

- it generates structured artifacts (research papers, proposals, analyses)
- these artifacts describe potential evolution
- artifacts are inspected, refined, and optionally approved
- only then can changes be applied

This principle must now become explicit doctrine.

TARGET

Update:

- "ARCHITECTURE_DOCTRINE_ADDENDUM.md"

Do NOT modify existing core doctrine files.

CREATE / EXTEND

Add a new section:

Brick 4 — Artifact-First Evolution Principle

REQUIRED CONTENT

SECTION — DEFINITION
Define clearly:

WESLR evolves through:

1. detection of inadequacy or opportunity
2. generation of structured artifact
3. exposure of reasoning and assumptions
4. operator / system feedback
5. governed application (optional)

Explicitly state:

- no direct self-modification
- no hidden mutation
- no implicit behavior drift

---

SECTION — WHY THIS EXISTS

Explain:

- prevents uncontrolled self-modification
- ensures inspectability and auditability
- enables learning across time
- aligns with continuity-first architecture
- allows multi-level understanding (operator → technical → research)

---

SECTION — ARTIFACT ROLE

Artifacts are:

- the unit of evolution
- the interface between reasoning and change
- the storage of WESLR’s thinking over time

Clarify types (high level only, no full taxonomy yet):

- research artifact
- improvement proposal
- analysis artifact

---

SECTION — RELATION TO EXISTING BRICKS

Connect explicitly:

- Context Selection Layer
 → ensures the RIGHT context is used before generating evolution artifacts

- Concept Boundary Model
 → prevents mixing systems in artifacts

- Continuity System
 → allows artifacts to build over time

- Contamination Control
 → ensures artifacts are based on correct context

---

SECTION — CONSTRAINTS

Explicitly forbid:

- direct runtime self-modification without artifact
- silent evolution
- artifact generation without traceable reasoning
- applying changes without governance path

---

SECTION — FUTURE EXTENSION

Mention but do not design:

- artifact types standardization
- A/B artifact comparison
- artifact lineage tracking
- research-grade outputs

---

SECTION — SHORT CANON STATEMENT

Add a short version:

«“WESLR evolves by externalizing its reasoning into structured artifacts, which are inspected and governed before any change is applied.”»

---

OUTPUT FORMAT

SECTION 1 — FILES CHANGED
SECTION 2 — COMMANDS RUN
SECTION 3 — DOCTRINE UPDATE SUMMARY
SECTION 4 — STOP LINE
assistant: ---

**SECTION 1 — FILES CHANGED**

| File | Action |
|---|---|
| `ARCHITECTURE_DOCTRINE_ADDENDUM.md` | Extended — Brick 4 section appended (added ~3,200 bytes) |

Existing doctrine files untouched.

---

**SECTION 2 — COMMANDS RUN**

None — documentation only.

---

**SECTION 3 — DOCTRINE UPDATE SUMMARY**

**Brick 4 — Artifact-First Evolution Principle** added to `ARCHITECTURE_DOCTRINE_ADDENDUM.md`:

- **Definition:** 5-step cycle — Detection → Artifact generation → Exposure → Feedback → Governed application. Explicit constraints: no direct self-modification, no hidden mutation, no implicit drift.
- **Why it exists:** Prevents uncontrolled modification; ensures inspectability/auditability; enables learning across time; aligns with continuity-first; enables multi-level operator understanding.
- **Artifact role:** Unit of evolution, interface between reasoning and change, storage of WESLR thinking over time. Three types noted (research, improvement proposal, analysis) — full taxonomy deferred.
- **Relation to existing bricks:** Context Selection Layer gates artifact quality (correct context → correct artifact); Concept Boundary Model prevents wrong-target artifacts; Continuity System enables artifact lineage; Contamination Control feeds diagnostic evidence into analysis artifacts.
- **Constraints:** Forbidden — direct runtime modification without artifact, silent evolution, reason-free artifacts, ungoverned application, self-authorizing "improvement."
- **Future extension:** Acknowledged but not designed — taxonomy, A/B comparison, lineage tracking, research-grade outputs.
- **Canon statement:** *«WESLR evolves by externalizing its reasoning into structured artifacts, which are inspected and governed before any change is applied.»*

---

**SECTION 4 — STOP LINE**

- Doctrine only. No code changes. No behavior changes.
- Additive to existing addendum.
- Short canon statement embedded in Section 4.
- Stop.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:32 GMT+2] WESLR — DESIGN NEXT CANON STEP
ARTIFACT TYPES AND LIFECYCLE V1

STRICT MODE

- design only
- no code changes
- no behavior changes
- no routing changes
- no scoring changes
- no governance changes
- no new authority
- additive only

AUTHORITATIVE CONTEXT

Brick 4 is now canonized in:

- "ARCHITECTURE_DOCTRINE_ADDENDUM.md"

Core principle:

- WESLR evolves by externalizing its reasoning into structured artifacts
- artifacts are inspected and governed before any change is applied

Now this needs structural canon around it.

GOAL

Define the canonical artifact model for WESLR:

- artifact types
- artifact roles
- artifact lifecycle
- allowed transitions
- relation to governance
- relation to SatUi / operators / future research surfaces

CREATE

"docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md"

READ FIRST

Only these:

- "ARCHITECTURE_DOCTRINE_ADDENDUM.md"
- "docs/SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md"
- "docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md"
- "docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md"
- "docs/WESLR_CANONICAL_SELF_MODEL_V1.md"

REQUIRED STRUCTURE

SECTION 1 — PURPOSE

- why Brick 4 needs explicit artifact structure
- why artifact types/lifecycle are needed before further expansion

SECTION 2 — CORE ARTIFACT TYPES
Define the main canonical artifact types.

At minimum consider:

- Research Artifact
- Analysis Artifact
- Improvement Proposal
- Comparison Artifact
- Judgment Artifact
- Continuity Artifact
- Boundary Clarification Artifact

For each:

- purpose
- what it contains
- who it is for
- whether it is observational, evaluative, comparative, or governance-relevant

SECTION 3 — ARTIFACT AUDIENCE LAYERS
Define how artifacts may serve:

- operator
- technical user
- researcher
- future system self-inspection

Keep this structural, not stylistic.

SECTION 4 — LIFECYCLE STATES
Define canonical states, for example:

- detected
- drafted
- surfaced
- reviewed
- refined
- approved
- denied
- archived
- lineage-linked

Choose the right set and justify.

SECTION 5 — ALLOWED TRANSITIONS
Define what transitions are allowed between artifact states and types.

Examples:

- analysis artifact → improvement proposal
- proposal → reviewed
- reviewed → approved/denied
- artifact A + artifact B → comparison artifact
- comparison artifact → judgment artifact

Explicitly forbid unsafe transitions.

SECTION 6 — RELATION TO GOVERNANCE
Define:

- which artifacts may enter governance
- which artifacts may only inform
- which artifacts must never directly trigger change

SECTION 7 — RELATION TO CONTINUITY
Explain how artifacts relate to:

- threads
- lineage
- active continuity objects
- timeline persistence

SECTION 8 — RELATION TO SATUI
Define how artifact types should appear in SatUi at a high level.
Do not design UI in detail.
Only define structural role:

- surfaced
- compared
- reviewed
- explained
- refined

SECTION 9 — FORBIDDEN DRIFT
Explicitly forbid:

- direct self-modification without artifact
- artifact type ambiguity collapsing governance
- skipping lifecycle states
- comparison without persistent references
- artifact mutation without lineage

SECTION 10 — RECOMMENDED FIRST IMPLEMENTATION
Choose the smallest safe structural implementation after design.

Likely:

- standardize artifact type field + lifecycle state field first
 or
- standardize type taxonomy before lifecycle automation

Choose one and justify.
You can spawn sub agents.
SECTION 11 — STOP LINE

- documentation only
- no code changes
- no behavior changes

OUTPUT FORMAT

SECTION 1 — FILES CHANGED
SECTION 2 — COMMANDS RUN
SECTION 3 — DESIGN SUMMARY
SECTION 4 — RECOMMENDED FIRST IMPLEMENTATION
SECTION 5 — STOP LINE
assistant: 

---

**SECTION 1 — FILES CHANGED**

| File | Action |
|---|---|
| `docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md` | **Created** — 28,690 bytes, 515+ lines |

---

**SECTION 2 — COMMANDS RUN**

None — design only.

---

**SECTION 3 — DESIGN SUMMARY**

**Six canonical artifact types:**
| Type | Purpose | Governance Role |
|---|---|---|
| Research Artifact | Investigate, document findings | None — informs only |
| Analysis Artifact | Diagnose gaps, surface problems | None — establishes gap |
| Improvement Proposal | Propose specific change | **Full governance** — ExecutionGate entry |
| Comparison Artifact | Compare options | None — enables decisions |
| Judgment Artifact | Record governance decision | Authoritative — IS the decision |
| Continuity Artifact | Maintain cross-session context | None — structural state |

**Lifecycle states:** `drafted → surfaced → reviewed → refined → approved/denied → applied/superseded → archived`

**Key design decisions:**
- Single linear state machine with `surfaced` as governance entry gate (not two parallel machines)
- Type taxonomy consolidates 5 parallel proposal schemas under Improvement Proposal type
- Forbidden transitions prevent: bypassing governance via type ambiguity, skipping lifecycle states, comparison without persistent references, artifact mutation without lineage
- Research/Analysis/Comparison/Continuity types may inform governance but never enter approval workflow directly

---

**SECTION 4 — RECOMMENDED FIRST IMPLEMENTATION**

**Choice: Standardize `artifact_type` + `artifact_state` fields first.**

Justification: Smallest safe structural step. Additive — existing artifacts and code remain valid. Enables future convergence as proposal generators are updated. Establishes the type/state contract before lifecycle automation.

**Immediate actions (design, not code):**
1. Define canonical field names in this document ✅ (Section 10)
2. Instrument `dialogue.py` research memo generation with type + state
3. Instrument `self_improvement_proposal.py` with type (`improvement_proposal`) + state
4. Instrument `cross_session_artifact_eval.py` with type (`analysis`) + state
5. SatUi reads and displays by type + state

**Defer:** Full artifact store, lifecycle automation, proposal schema normalization.

---

**SECTION 5 — STOP LINE**

- Design only. No code changes. No behavior changes.
- New canonical document: `docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md` ✅
- Extends Brick 4 (Artifact-First Evolution Principle) with explicit taxonomy and lifecycle
- Aligns with SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md, CONTINUITY_CONTAMINATION_CONTROL_V1.md, TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md, WESLR_CANONICAL_SELF_MODEL_V1.md
- Stop.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:38 GMT+2] WESLR — DESIGN NEXT CANON STEP
ARTIFACT LINEAGE AND GRAPH MODEL V1

STRICT MODE

- design only
- no code changes
- no behavior changes
- no routing changes
- no scoring changes
- no governance changes
- no new authority
- additive only

AUTHORITATIVE CONTEXT

Existing canon now includes:

- "ARCHITECTURE_DOCTRINE_ADDENDUM.md" (Brick 4 — Artifact-First Evolution Principle)
- "docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md"

Current state:

- artifact types are defined
- artifact lifecycle is defined
- governance boundary is defined
- but artifact lineage is not yet first-class
- comparisons, proposals, judgments, and continuity artifacts need explicit structural ancestry

GOAL

Define the canonical lineage and graph model for artifacts so WESLR can trace:

- where an artifact came from
- what it depends on
- what it influenced
- how artifact chains evolve over time

CREATE

"docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md"

READ FIRST

Only these:

- "ARCHITECTURE_DOCTRINE_ADDENDUM.md"
- "docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md"
- "docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md"
- "docs/WESLR_CANONICAL_SELF_MODEL_V1.md"

REQUIRED STRUCTURE

SECTION 1 — PURPOSE

- why artifact lineage is required after types/lifecycle
- why artifacts must not remain isolated objects
- why lineage is necessary for auditability, comparison, and future synthesis

SECTION 2 — CORE LINEAGE PRINCIPLE
Define the rule:

- every artifact must have traceable origin
- first-generation artifacts may point to origin event/source instead of parent artifact
- derived artifacts must explicitly reference parent artifact(s)

Distinguish:

- root artifact
- derived artifact
- multi-parent artifact

SECTION 3 — GRAPH MODEL
Define the artifact graph at a structural level.

At minimum define:

- node = artifact
- edge = relationship

Candidate edge types:

- "derived_from"
- "compares"
- "judges"
- "refines"
- "analyzes"
- "proposes_change_for"
- "continues"
- "supersedes"

For each:

- meaning
- allowed source/target types

SECTION 4 — REQUIRED LINEAGE FIELDS
Define the minimum canonical fields, for example:

- "artifact_id"
- "artifact_type"
- "artifact_state"
- "origin_event"
- "origin_artifact_id"
- "parent_artifact_ids"
- "root_artifact_id"
- "lineage_depth"
- "graph_edges"

Choose the right set and justify.

SECTION 5 — STATE VS AUTHORITY
Explicitly define:

- artifact lineage/state does NOT grant execution authority
- "approved" does not mean “may self-apply”
- graph connectivity does not imply permission

SECTION 6 — RELATION TO ARTIFACT TYPES
Explain how lineage behaves for each canonical type:

- Research Artifact
- Analysis Artifact
- Improvement Proposal
- Comparison Artifact
- Judgment Artifact
- Continuity Artifact

SECTION 7 — RELATION TO CONTINUITY
Explain how lineage relates to:

- threads
- active continuity object
- timeline persistence
- future cross-session reference resolution

SECTION 8 — FORBIDDEN DRIFT
Explicitly forbid:

- artifact mutation without lineage update
- comparison without persistent references
- derived artifacts with no parent trace
- lineage graph being used as execution authority
- silent rewriting of root/parent relationships

SECTION 9 — RECOMMENDED FIRST IMPLEMENTATION
Choose the smallest safe structural implementation.
Likely:

- add canonical lineage fields first
- defer full graph querying/visualization
- do not automate lineage inference broadly yet

SECTION 10 — FUTURE EXTENSIONS
Mention but do not design fully:

- graph querying
- synthesis artifacts
- lineage-aware SatUi displays
- multi-artifact research chains

SECTION 11 — STOP LINE

- documentation only
- no code changes
- no behavior changes

OUTPUT FORMAT

SECTION 1 — FILES CHANGED
SECTION 2 — COMMANDS RUN
SECTION 3 — DESIGN SUMMARY
SECTION 4 — RECOMMENDED FIRST IMPLEMENTATION
SECTION 5 — STOP LINE
assistant: 

---

**SECTION 1 — FILES CHANGED**

| File | Action |
|---|---|
| `docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md` | **Created** — 29,067 bytes, 471+ lines |

---

**SECTION 2 — COMMANDS RUN**

None — design only.

---

**SECTION 3 — DESIGN SUMMARY**

**Core lineage principle:** Every artifact has a traceable origin — root artifacts point to `origin_event`/`origin_source`; derived artifacts point to `parent_artifact_ids`. No orphan artifacts.

**Graph model:** Directed acyclic graph (DAG). Nodes = artifacts. Edges = 8 types: `derived_from`, `compares`, `judges`, `refines`, `analyzes`, `proposes_change_for`, `continues`, `supersedes`. Edge cardinality defined per type. Cycles are forbidden.

**Required fields:** `artifact_id`, `artifact_type`, `artifact_state`, `origin_event`, `origin_source`, `parent_artifact_ids`, `root_artifact_id`, `lineage_depth`, `generation`, `graph_edges`, `origin_reason` (multi-parent only).

**State vs Authority:** Explicitly separated. `approved` state is a governance record, not an execution permit. Graph connectivity provides traceability, not authority. No edge type grants execution rights.

**Per type behavior:**
- Research: root common, multi-parent allowed (synthesis)
- Analysis: typically single-parent, edge `analyzes`
- Improvement Proposal: typically single-parent from Analysis, edge `proposes_change_for`
- Comparison: required multi-parent (≥2 options), edge `compares`
- Judgment: single-parent from target, edge `judges`
- Continuity: root preferred, no multi-parent, edges `continues`/`supersedes`

**Relation to continuity:** Thread and lineage are orthogonal dimensions. Active continuity object can reference artifact with lineage. Timeline log records lineage events.

---

**SECTION 4 — RECOMMENDED FIRST IMPLEMENTATION**

**Choice: Add canonical lineage fields to new artifacts; leave existing artifacts unchanged.**

Justification: Smallest safe step. Fields live in artifact JSON — no graph store, no edge database, no query engine needed yet. Backward compatible. Establishes contract before graph automation.

**Fields to add:** `root_artifact_id`, `parent_artifact_ids`, `lineage_depth`, `generation`, `origin_event`, `origin_source`, `graph_edges`, `origin_reason`

**Order:**
1. Document field definitions ✅ (this design)
2. Instrument `dialogue.py` artifact creation with all lineage fields
3. Instrument `self_improvement_proposal.py` with lineage fields
4. Instrument `cross_session_artifact_eval.py` with lineage fields

**Defer:** Graph store, graph query engine, cycle detection, lineage visualization in SatUi, retroactive lineage for existing artifacts.

---

**SECTION 5 — STOP LINE**

- Design only. No code changes. No behavior changes.
- New canonical document: `docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md` ✅
- Extends ARTIFACT_TYPES_AND_LIFECYCLE_V1 with ancestry and graph structure
- Aligns with ARCHITECTURE_DOCTRINE_ADDENDUM.md (Brick 4 traceability), TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md (thread/lineage orthogonal), WESLR_CANONICAL_SELF_MODEL_V1.md (7-lane consolidation target)
- Stop.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:42 GMT+2] WESLR — STRENGTHEN ARTIFACT LINEAGE CANON
ADD NON-AUTHORITY INVARIANT

STRICT MODE

- documentation only
- no code changes
- no behavior changes
- additive only
- do not redesign the document
- only strengthen the existing canon with the non-authority invariant

TARGET

Update:

- "docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md"

GOAL

Reinforce the rule:

Artifact state and artifact lineage are descriptive, not authoritative.

This rule must become a system-wide invariant inside the lineage/graph canon, not just a local note.

REQUIRED CHANGES

Add or strengthen this rule in exactly these places:

1. SECTION 2 — CORE LINEAGE PRINCIPLE

Add a short paragraph clarifying:

- lineage provides traceability
- lineage does not grant permission
- artifact history/status do not authorize execution

Suggested text:

«Artifact state and artifact lineage are descriptive, not authoritative. They describe what is true about an artifact’s history and status, but they do not grant permission to execute, apply, or mutate system behavior.»

2. SECTION 3 — GRAPH MODEL

Add a short paragraph clarifying:

- graph edges are structural relationships only
- graph connectivity never implies execution authority
- lineage depth, parent count, or edge richness never grant permission

Suggested text:

«Graph relationships define structural connections between artifacts. Artifact state and artifact lineage are descriptive, not authoritative. No edge type, graph connectivity, or lineage depth implies execution authority or permission to act.»

3. SECTION 5 — STATE VS AUTHORITY

Strengthen this section by making the invariant explicit at the top.

Required content:

- artifact state is a recorded status
- artifact lineage is traceability
- neither grants authority
- execution authority exists only through explicit governance mechanisms outside the artifact structure

Use this exact first line if helpful:

«Artifact state and artifact lineage are descriptive, not authoritative.»

4. SECTION 8 — FORBIDDEN DRIFT

Add a new explicit forbidden-drift rule:

No implicit authority from state or lineage

It must forbid:

- treating "approved" as automatic permission to apply changes
- treating strong lineage / many parents / deep chains as justification for execution
- using graph connectivity as an execution trigger

Suggested wording:

«Artifact state and artifact lineage must never be used to infer execution authority. All execution must pass through explicit governance pathways.»

OUTPUT FORMAT

SECTION 1 — FILES CHANGED
SECTION 2 — COMMANDS RUN
SECTION 3 — EXACT CHANGES MADE
SECTION 4 — STOP LINE

STOP AFTER DOCUMENT UPDATE
No code changes.
No architecture redesign.
assistant: 

---

**SECTION 1 — FILES CHANGED**

| File | Action |
|---|---|
| `docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md` | Modified — 4 targeted additions |

---

**SECTION 2 — COMMANDS RUN**

None — documentation only.

---

**SECTION 3 — EXACT CHANGES MADE**

**Change 1 — Section 2, Core Lineage Principle, after "Every artifact must have a traceable origin":**
```
Artifact state and artifact lineage are descriptive, not authoritative. They describe what is true about an artifact's history and status, but they do not grant permission to execute, apply, or mutate system behavior.
```

**Change 2 — Section 3, Graph Model, after "Cycle Prohibition" paragraph:**
```
Graph relationships define structural connections between artifacts. Artifact state and artifact lineage are descriptive, not authoritative. No edge type, graph connectivity, or lineage depth implies execution authority or permission to act.
```

**Change 3 — Section 5, State vs Authority, first paragraph replaced:**
```
Artifact state and artifact lineage are descriptive, not authoritative.

Artifact state is a recorded status. Artifact lineage is traceability. Neither grants authority. Execution authority exists only through explicit governance mechanisms outside the artifact structure.
```
*(rest of section 5 unchanged)*

**Change 4 — Section 8, Forbidden Drift, new rule added after F7:**
```
F8 — No Implicit Authority from State or Lineage

Artifact state and artifact lineage must never be used to infer execution authority. All execution must pass through explicit governance pathways. Specifically:
- "approved" state does not mean the change may self-apply — execution still requires ExecutionGate verification
- Strong lineage, many parents, or deep chains never justify execution without approval
- Graph connectivity (edge types, connectivity patterns, lineage depth) never triggers or authorizes execution
- Using graph position or edge presence as an execution trigger violates this invariant
```

---

**SECTION 4 — STOP LINE**

- Documentation only ✅
- No code changes ✅
- No behavior changes ✅
- Additive only — existing content preserved ✅
- Stop.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:46 GMT+2] WESLR — INSPECT EXISTING LINEAGE / RELATIONSHIP SURFACES

STRICT MODE

- inspection only
- no code changes
- no design
- no refactoring
- no proposals
- report only what exists in code and runtime

GOAL

Before designing lineage visibility or SatUi features, map:

- what lineage-like data already exists
- what relationship structures already exist
- what is already surfaced to UI
- what is duplicated or fragmented

Do NOT assume anything.
Do NOT suggest improvements.
Only report.

SCOPE — READ ONLY

Search in:

- "dialogue.py"
- "chat_ui.py"
- "weslr/artifact_store.py"
- "weslr/timeline_resolution.py"
- "weslr/thread_tracker.py"
- "weslr/cross_session_artifact_eval.py"
- "weslr/relevance_eval_analysis.py"
- "continuity/artifacts/"
- any "*_eval*.py"
- any files referencing:
 - artifact
 - parent
 - lineage
 - thread
 - relation
 - derived
 - compare
 - judge

TASKS

SECTION 1 — EXISTING LINEAGE DATA

List ALL fields already present in artifacts or eval artifacts that represent:

- parent relationships
- origin
- derivation
- continuation
- replacement

Example categories:

- parent_artifact_ids
- origin_event
- root_artifact_id
- graph_edges
- artifact_ids_involved
- session_sequence
- anything similar

For each:

- file
- field name
- where written
- where read (if anywhere)

---

SECTION 2 — EXISTING RELATIONSHIP LOGIC

Identify where relationships are already used:

- artifact → artifact
- thread → artifact
- session → artifact
- eval → artifact
- proposal → analysis

List:

- function name
- file
- what relationship it implies

---

SECTION 3 — EXISTING “LINEAGE-LIKE” SURFACES

Find anything already acting like lineage even if not called that:

Examples:

- thread history
- active artifact resolution
- eval artifact chains
- comparison artifacts
- contamination references

Explain:

- what it represents
- how close it is to real lineage

---

SECTION 4 — WHAT IS ALREADY EXPOSED TO UI

From "chat_ui.py" and any related code:

List what is already sent to UI:

- artifact IDs?
- artifact content?
- contamination metadata?
- any relationships?

Important:

- what is visible
- what is hidden but available

---

SECTION 5 — DUPLICATION / FRAGMENTATION

Identify if relationships are spread across:

- multiple files
- multiple formats
- inconsistent naming

Examples:

- same concept represented differently
- same relationship tracked in two places

---

SECTION 6 — GAP SUMMARY (FACTUAL ONLY)

List gaps WITHOUT proposing solutions:

- missing connections
- data present but not used
- surfaces present but not unified

---

OUTPUT FORMAT

SECTION 1 — FILES READ
SECTION 2 — EXISTING LINEAGE DATA
SECTION 3 — RELATIONSHIP LOGIC
SECTION 4 — LINEAGE-LIKE SURFACES
SECTION 5 — UI EXPOSURE
SECTION 6 — DUPLICATION / FRAGMENTATION
SECTION 7 — GAP SUMMARY
SECTION 8 — STOP LINE

STOP AFTER REPORT

Do NOT design.
Do NOT fix.
Do NOT propose.
Only report what exists.
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Wed 2026-04-22 22:46 GMT+2] WESLR — INSPECT EXISTING LINEAGE / RELATIONSHIP SURFACES

STRICT MODE

- inspection only
- no code changes
- no design
- no refactoring
- no proposals
- report only what exists in code and runtime

GOAL

Before designing lineage visibility or SatUi features, map:

- what lineage-like data already exists
- what relationship structures already exist
- what is already surfaced to UI
- what is duplicated or fragmented

Do NOT assume anything.
Do NOT suggest improvements.
Only report.

SCOPE — READ ONLY

Search in:

- "dialogue.py"
- "chat_ui.py"
- "weslr/artifact_store.py"
- "weslr/timeline_resolution.py"
- "weslr/thread_tracker.py"
- "weslr/cross_session_artifact_eval.py"
- "weslr/relevance_eval_analysis.py"
- "continuity/artifacts/"
- any "*_eval*.py"
- any files referencing:
 - artifact
 - parent
 - lineage
 - thread
 - relation
 - derived
 - compare
 - judge

TASKS

SECTION 1 — EXISTING LINEAGE DATA

List ALL fields already present in artifacts or eval artifacts that represent:

- parent relationships
- origin
- derivation
- continuation
- replacement

Example categories:

- parent_artifact_ids
- origin_event
- root_artifact_id
- graph_edges
- artifact_ids_involved
- session_sequence
- anything similar

For each:

- file
- field name
- where written
- where read (if anywhere)

---

SECTION 2 — EXISTING RELATIONSHIP LOGIC

Identify where relationships are already used:

- artifact → artifact
- thread → artifact
- session → artifact
- eval → artifact
- proposal → analysis

List:

- function name
- file
- what relationship it implies

---

SECTION 3 — EXISTING “LINEAGE-LIKE” SURFACES

Find anything already acting like lineage even if not called that:

Examples:

- thread history
- active artifact resolution
- eval artifact chains
- comparison artifacts
- contamination references

Explain:

- what it represents
- how close it is to real lineage

---

SECTION 4 — WHAT IS ALREADY EXPOSED TO UI

From "chat_ui.py" and any related code:

List what is already sent to UI:

- artifact IDs?
- artifact content?
- contamination metadata?
- any relationships?

Important:

- what is visible
- what is hidden but available

---

SECTION 5 — DUPLICATION / FRAGMENTATION

Identify if relationships are spread across:

- multiple files
- multiple formats
- inconsistent naming

Examples:

- same concept represented differently
- same relationship tracked in two places

---

SECTION 6 — GAP SUMMARY (FACTUAL ONLY)

List gaps WITHOUT proposing solutions:

- missing connections
- data present but not used
- surfaces present but not unified

---

OUTPUT FORMAT

SECTION 1 — FILES READ
SECTION 2 — EXISTING LINEAGE DATA
SECTION 3 — RELATIONSHIP LOGIC
SECTION 4 — LINEAGE-LIKE SURFACES
SECTION 5 — UI EXPOSURE
SECTION 6 — DUPLICATION / FRAGMENTATION
SECTION 7 — GAP SUMMARY
SECTION 8 — STOP LINE

STOP AFTER REPORT

Do NOT design.
Do NOT fix.
Do NOT propose.
Only report what exists.
