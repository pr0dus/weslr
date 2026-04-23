# ARTIFACT TYPES AND LIFECYCLE V1
**Generated:** 2026-04-22 22:32 GMT+2
**Mode:** STRICT — design only, no code changes, no behavior changes, no routing changes, no scoring changes, no governance changes
**Author:** Main agent
**Sources:** ARCHITECTURE_DOCTRINE_ADDENDUM.md (Brick 4), SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md, CONTINUITY_CONTAMINATION_CONTROL_V1.md, TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md, WESLR_CANONICAL_SELF_MODEL_V1.md

---

## SECTION 1 — PURPOSE

### Why Brick 4 Needs Explicit Artifact Structure

Brick 4 (Artifact-First Evolution Principle) established the rule: *WESLR evolves by externalizing its reasoning into structured artifacts, which are inspected and governed before any change is applied.* This rule creates the artifact as the mandatory intermediary between reasoning and change.

But Brick 4 did not define:
- What kinds of artifacts exist
- What role each kind serves
- How artifacts move from creation to decision
- When artifacts may trigger governance and when they may not
- How artifacts relate to threads, timelines, and continuity objects
- How artifacts should surface in SatUi

Without these definitions, Artifact-First Evolution degenerates into a vague principle. Any document could be called an "artifact." Any output could claim to be an evolution step. Without explicit type contracts and lifecycle states, the "artifact" concept cannot be used as a governance tool.

### Why Types and Lifecycle Are Needed Before Further Expansion

The current WESLR reality (documented in WESLR_CANONICAL_SELF_MODEL_V1.md) includes:
- 5 independent proposal generators with different schemas
- Artifacts that serve 5 overlapping roles (reasoning unit, research output, evaluation, communication, comparison)
- 7 parallel self-improvement lanes with no unified core
- No artifact-to-proposal bridge

This is the fragmentation that explicit artifact types and lifecycle rules are designed to prevent. Types create natural consolidation targets: "Analysis Artifact" collects all evaluative outputs regardless of which system generated them. Lifecycle states create governance hooks: only artifacts in `surfaced` or `reviewed` states may enter governance review.

Without types and lifecycle, expansion means more parallel systems. With them, expansion means extending an existing contract.

---

## SECTION 2 — CORE ARTIFACT TYPES

### Design Principle

Each artifact type is defined by its **purpose** (why it exists), **contents** (what it contains), **audience** (who it is for), and **evaluation mode** (how it should be read by governance reviewers).

Types do not correspond to file formats. A Research Artifact might be stored as JSON, Markdown, or both. A Comparison Artifact might be rendered as text in SatUi. Type is a semantic role, not a storage format.

### Type 1 — Research Artifact

**Purpose:** Explore a topic, document findings, expose reasoning and assumptions. The primary output of WESLR's curiosity-driven and adequacy-driven research cycles.

**What it contains:**
- Hypothesis or question being investigated
- Evidence gathered (with source references)
- Reasoning chain (how evidence was interpreted)
- Alternative interpretations considered and rejected
- Confidence level and reasoning for the estimate
- Limitations and known gaps
- Next experiment or investigation path

**Who it is for:**
- Operator (high-level: is this worth acting on?)
- Researcher (detailed: what did WESLR find and how?)
- Future system self-inspection (lineage: does this build on or contradict prior research?)

**Evaluation mode:** Observational. Research Artifacts describe the world as WESLR understands it. They do not recommend action. They inform decisions made elsewhere.

**Examples:** Domain investigation memo, contamination pattern analysis, self-eval finding document.

---

### Type 2 — Analysis Artifact

**Purpose:** Evaluate existing WESLR behavior, surface problems or opportunities, diagnose symptoms and their likely causes. The primary output of diagnostic and diagnostic-synthesis cycles.

**What it contains:**
- Behavior or state being analyzed
- Observed symptoms
- Root cause hypothesis (with confidence level)
- Evidence supporting the hypothesis
- Alternative explanations considered
- Severity assessment (impact if not addressed)
- Relation to other known issues

**Who it is for:**
- Operator (is this a real problem worth addressing?)
- Technical reviewer (does the diagnosis make sense?)
- Future self-inspection (has this pattern recurred?)

**Evaluation mode:** Evaluative. Analysis Artifacts state whether something is adequate or inadequate and why. They carry diagnostic weight, but do not prescribe specific changes. They establish the gap; Improvement Proposals name the fix.

**Examples:** `csc-eval-*.json` contamination evaluation, adequacy threshold breach analysis, drift concern document.

---

### Type 3 — Improvement Proposal

**Purpose:** Identify a specific gap and propose a concrete change to address it. The primary output of the governed evolution cycle. The only artifact type that may enter formal governance (approval/denial workflow).

**What it contains:**
- Gap being addressed (reference to Analysis Artifact or direct problem statement)
- Proposed change (specific enough to inspect and evaluate)
- Evidence that the gap is real and the change would address it
- Confidence in the fix
- Alternative approaches considered and why this was chosen
- Risk of the change (what could go wrong if applied)
- Rollback path (how to reverse if needed)
- Relation to existing artifacts (which Research/Analysis Artifacts informed this)

**Who it is for:**
- Operator (approve/deny decision)
- Governance system (ExecutionGate review)
- Future system (was this proposal effective? did it actually fix the gap?)

**Evaluation mode:** Governance-relevant. This type is the gate-keeper for actual system changes. It must contain everything needed for a reviewed decision: what changed, why, what could go wrong, how to reverse.

**Examples:** CDI improvement proposal, self-mod proposal, configuration change proposal.

**Note:** All existing proposal schemas (InsightProposalPayload, ChangeProposal, improvement_engine dict, self_eval dict) should normalize to this type when entering the governance pipeline. Fragmentation is addressed by type convergence, not type proliferation.

---

### Type 4 — Comparison Artifact

**Purpose:** Evaluate two or more options against each other and produce a structured comparison result. The output of A/B evaluation and option comparison cycles.

**What it contains:**
- Reference to the options being compared (option IDs, generation context)
- Assessment criteria (what dimensions are being compared)
- Comparison analysis (how each option scores on each criterion)
- Winner determination or declaration of no winner
- Reasoning for the comparison outcome
- Dissenting view or alternative winner interpretation (if applicable)

**Who it is for:**
- Operator (which option should be approved?)
- Technical reviewer (is the comparison methodology sound?)
- Future system (has this comparison pattern been replicated?)

**Evaluation mode:** Comparative, not autonomous. Comparison Artifacts enable decisions; they do not make them. The `winner` field may be null — comparison without a determined winner is valid. The operator decides.

**Examples:** Option A vs Option B artifact comparison, two Improvement Proposal variants compared, before/after behavior comparison.

---

### Type 5 — Judgment Artifact

**Purpose:** Record a governance decision on a target artifact. The durable audit record of operator (or system) decision on an artifact that entered governance review.

**What it contains:**
- Reference to the target artifact (ID and type)
- Decision: `approved` | `denied` | `superseded` | `needs_revision`
- Reason for the decision (plain language)
- Who made the judgment (operator_id or `system`)
- When the judgment was made (timestamp)
- Institution scope (if applicable)
- Audit reference (link to audit ledger entry)

**Who it is for:**
- Operator (what decisions have been made and why?)
- Governance system (what has been approved or rejected?)
- Future system (what is the current authoritative version of this artifact?)

**Evaluation mode:** Governance. Judgment Artifacts are the permanent record of decisions. They are not arguments for or against something — they are the decisions themselves. They are always authoritative; they do not propose.

**Examples:** Proposal approval record, comparison winner record, artifact supersession record.

---

### Type 6 — Continuity Artifact

**Purpose:** Maintain cross-session and cross-thread continuity state. Represents the continuity layer's understanding of threads, artifacts, and context relationships.

**What it contains:**
- Reference to continuity objects (thread_id, artifact_id, timeline_event)
- Relationship type (links, supersedes, references, evolves)
- Continuity scope (user, institution, global)
- Metadata for resolution context (domain, generation, authorization level)

**Who it is for:**
- Operator (what is the active continuity context?)
- WESLR runtime (what should "this" resolve to?)
- Future system self-inspection (what was the continuity state at time X?)

**Evaluation mode:** Observational / structural. Continuity Artifacts describe relationships between objects; they do not make arguments or recommendations. They are the canonical answer to "what is the current continuity context?"

**Examples:** Active thread snapshot, lineage chain record, context selection decision record.

---

### Type Summary Table

| Type | Purpose | Governance Role | Evaluation Mode |
|---|---|---|---|
| Research Artifact | Investigate and document findings | None — informs only | Observational |
| Analysis Artifact | Diagnose behavior and surface gaps | None — establishes gap, does not prescribe fix | Evaluative |
| Improvement Proposal | Propose specific change | Full governance — may enter ExecutionGate | Governance-relevant |
| Comparison Artifact | Compare options | None — enables decisions, does not make them | Comparative |
| Judgment Artifact | Record governance decision | Authoritative — is the decision itself | Authoritative |
| Continuity Artifact | Maintain continuity context | None — structural state record | Observational / structural |

---

## SECTION 3 — ARTIFACT AUDIENCE LAYERS

Artifacts serve four distinct audience layers. Each layer reads the same artifact differently.

| Layer | What They Read | What They Do With It |
|---|---|---|
| **Operator** | High-level summary and decision-relevant content (gap statement, proposed change, risk, rollback path) | Approve / deny / refine improvement proposals; review comparison artifacts |
| **Technical User** | Full reasoning, evidence chain, alternative interpretations | Evaluate whether the diagnosis or proposal is technically sound; identify logical gaps |
| **Researcher** | Complete record: evidence, reasoning, assumptions, limitations, next steps | Trace how conclusions were reached; build on prior research; identify recurring patterns |
| **Future System Self-Inspection** | Structured metadata: type, lineage, creation time, decision state, relationship references | Determine whether this artifact has been superseded; whether it informs current work; how patterns recur over time |

### Structural Implication

Every artifact type must support being read at the Operator level (high-level scan) without requiring the full detail. This does not mean shortening artifacts — it means the artifact structure itself must have a clear high-level summary that can be read in under 30 seconds, with full detail available on demand.

Research-paper style format (hypothesis → evidence → reasoning → limitations → next steps) already satisfies this: the hypothesis is the Operator summary; the rest is technical detail.

---

## SECTION 4 — LIFECYCLE STATES

### Design Decision: Single-State Machine with Governance Entry Point

A single linear state machine with one designated entry gate. Not two parallel state machines (one for evolution progression, one for governance readiness). The single machine handles both because governance review is the primary evolution gate.

The entry point is `drafted`. All artifacts begin in `drafted`. From there, they move forward through the lifecycle. Backward transitions are not allowed — if an artifact needs modification, it moves to `refined` from `surfaced` or `reviewed`, not backward.

### Canonical States

| State | Meaning |
|---|---|
| `drafted` | Artifact created; reasoning and content assembled; not yet exposed for review |
| `surfaced` | Artifact ready for operator/system review; all required fields populated; awaiting review |
| `reviewed` | Operator or system has examined the artifact; feedback exists but not yet incorporated |
| `refined` | Feedback from review has been incorporated; artifact updated; returned to `surfaced` or `approved`/`denied` |
| `approved` | Governance decision: change authorized to proceed (Improvement Proposals only) |
| `denied` | Governance decision: change not authorized |
| `applied` | Change has been executed (Improvement Proposals that were approved) |
| `superseded` | A newer artifact has replaced this one (lineage continuation) |
| `archived` | Artifact preserved for record; no longer active; available for inspection |

### State Transition Rules

| From | To | Condition |
|---|---|---|
| `drafted` | `surfaced` | All required fields for the artifact type are populated; content is complete |
| `surfaced` | `reviewed` | Operator or system has opened review |
| `reviewed` | `refined` | Feedback received; requires modification before re-review |
| `reviewed` | `approved` | Governance decision: approved (Improvement Proposal only) |
| `reviewed` | `denied` | Governance decision: denied |
| `approved` | `applied` | Execution complete; audit record created |
| `surfaced` | `superseded` | Newer artifact in same lineage chain has been `approved` |
| `surfaced` | `archived` | Operator or system archived without decision |
| Any | `archived` | Final state; artifact preserved but inactive |

### Governance Entry Gate

Only `surfaced` artifacts may enter governance review. An artifact in `drafted` cannot be approved or denied — it must first reach `surfaced`. This prevents premature governance requests on incomplete artifacts.

The transition `drafted → surfaced` is a WESLR-internal gate: WESLR declares the artifact complete. This does not require operator action — it is the artifact author's signal that the artifact is ready.

---

## SECTION 5 — ALLOWED TRANSITIONS

### Type Transitions (Artifact Type → Artifact Type)

| From | To | Condition |
|---|---|---|
| Research Artifact | Analysis Artifact | Research findings identify a gap that warrants diagnosis |
| Analysis Artifact | Improvement Proposal | Analysis establishes a gap that warrants a specific fix proposal |
| Analysis Artifact | Research Artifact | Analysis identifies a knowledge gap requiring further research |
| Comparison Artifact | Judgment Artifact | Comparison enables a decision; judgment records the decision |
| Comparison Artifact | Improvement Proposal | Comparison identifies a preferred option; proposal formalizes the change |
| Research Artifact | Improvement Proposal | Direct path when research findings directly motivate a change (skipping Analysis as a separate artifact, if analysis is minimal) |
| Improvement Proposal | Analysis Artifact | Post-application analysis: did the change actually work? |
| Any Artifact | Comparison Artifact | Any artifacts may be compared (A/B comparison) |
| Any Surface Artifact | Judgment Artifact | Any artifact in `surfaced` state may be judged |

### Forbidden Transitions

| Forbidden Transition | Reason |
|---|---|
| Research → Improvement without governance review | All proposals must enter governance; type transition alone does not satisfy this |
| Improvement Proposal → executed without `approved` state | Execution requires explicit approval; no bypass |
| Comparison Artifact → auto-determination of winner | Comparison enables decisions; it does not make them |
| Any → `applied` without going through `approved` | The approval gate is non-negotiable |
| Skipping `drafted` → `surfaced` → governance | Incomplete artifacts cannot enter governance; this protects operator from premature reviews |
| Artifact mutation after `approved` | An approved artifact must not be modified; create a new artifact with lineage link instead |
| Archiving an `approved` artifact without executing | Approval without execution should be rare; must be explicitly recorded |

### Lineage Transitions

When a new artifact replaces an older one in the same chain:
- New artifact: `surfaced` (or `approved` if immediate governance path)
- Old artifact: transitions to `superseded`
- The `parent_artifact_id` field links the chain

This replaces the old artifact without destroying the record. Comparison artifacts and judgment artifacts create lineage entries even when they do not supersede — they reference what they evaluated.

---

## SECTION 6 — RELATION TO GOVERNANCE

### Which artifact types may enter governance

| Type | May Enter Governance | How |
|---|---|---|
| Research Artifact | No — informational only | Informs proposals; does not itself trigger change |
| Analysis Artifact | No — diagnostic only | Establishes gap; does not prescribe specific change |
| Improvement Proposal | **Yes — full governance** | Enters ExecutionGate review; approval required before execution |
| Comparison Artifact | No — comparative only | Informs judgment; does not make decision |
| Judgment Artifact | **Authoritative record** | Is the governance outcome itself; does not enter review |
| Continuity Artifact | No — structural only | Describes continuity state; no governance relevance |

### Improvement Proposal Governance Path

```
drafted → surfaced (WESLR declares complete)
surfaced → reviewed (operator/system opens review)
reviewed → refined (feedback → new version → surfaced)
reviewed → approved (ExecutionGate: approved)
approved → applied (execution + audit entry)
```

### What Happens to Non-Governance Artifacts

Research, Analysis, Comparison, and Continuity artifacts do not disappear after creation. They persist:
- Research artifacts build the knowledge base for future research
- Analysis artifacts inform Improvement Proposals
- Comparison artifacts are referenced by Judgment artifacts
- Continuity artifacts maintain cross-session state

These types may inform governance decisions without entering the approval workflow.

---

## SECTION 7 — RELATION TO CONTINUITY

### Thread Integration

Artifacts are linked to threads via `thread_id` in artifact metadata. A thread is a sequence of artifacts (and other items). An artifact's `thread_id` field establishes which thread it belongs to.

Thread resolution: "improve this" resolves to the most recent `active` artifact in the active thread. This requires the artifact to have been written to the artifact store with `thread_id` populated.

### Lineage Integration

Each artifact may have a `parent_artifact_id` (direct parent) and a `root_artifact_id` (origin of the chain). The `generation` field indicates position in the chain.

Lineage rules:
- An artifact in `superseded` state may still be referenced (it is historical record)
- An `approved` artifact supersedes its parent when a newer generation exists
- Comparison artifacts record which artifacts in the lineage they compared

### Timeline Integration

Artifact lifecycle events are written to the timeline event log:
- `artifact.created` — when artifact enters `drafted` state
- `artifact.surfaced` — when artifact becomes available for review
- `artifact.decision` — when judgment is recorded (`approved`, `denied`, `archived`)
- `artifact.applied` — when Improvement Proposal is executed
- `artifact.superseded` — when newer artifact enters the chain

This creates a queryable history of artifact lifecycle for any timestamp.

### Active Continuity Object

The active continuity object (per TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md) may reference an artifact as its current focus. When an artifact is the current focus of the active continuity object:
- It is the resolution target for "improve this"
- It is visible in SatUi as the active working artifact
- Its `thread_id` is the active thread

Contamination control (per CONTINUITY_CONTAMINATION_CONTROL_V1.md) attaches contamination metadata to artifacts at resolution time. The `_contamination_metadata` field is stored alongside artifact metadata when present.

---

## SECTION 8 — RELATION TO SATUI

### Structural Role of Artifacts in SatUi

SatUi is the operator-facing surface. Artifacts appear in SatUi in five structural roles:

| Role | Description | Artifact Types Involved |
|---|---|---|
| **surfaced** | Artifact presented to operator for review | All `surfaced` artifacts; Improvement Proposals most prominent |
| **compared** | Option A vs Option B presented for judgment | Comparison Artifact → displayed as comparison pair |
| **reviewed** | Judgment made; result recorded | Judgment Artifact displayed as decision record |
| **explained** | Lineage and context shown for transparency | Continuity Artifact + Research Artifact shown with lineage |
| **refined** | Revision request returned to operator | Analysis or Research artifact prompts revision cycle |

### What SatUi Does NOT Do (By Type Contract)

- SatUi does not make governance decisions — it surfaces artifacts for operator review and records judgments
- SatUi does not generate artifacts — it receives and displays what WESLR produces
- SatUi does not bypass governance — "improve this" in SatUi generates a proposed revision in `surfaced` state; operator review required before it becomes active
- SatUi does not show artifacts outside the operator's authorized scope

### Display by Risk Level

Contamination metadata (per SATUI_CONTAMINATION_DISPLAY_V1.md) appears on artifacts with `risk_level: medium` or `high`:
- Amber advisory for `medium`: type label, collapsed reason
- Red advisory for `high`: type label, visible reason, expandable source signals

This display is independent of artifact type — contamination advisory applies to any artifact with contamination metadata.

---

## SECTION 9 — FORBIDDEN DRIFT

### F1 — No Direct Runtime Self-Modification Without Artifact

The Artifact-First Evolution rule is absolute. Any change to production state must be traceable to an Improvement Proposal artifact that received `approved` judgment. No silent writes. No direct code modification without artifact intermediary.

### F2 — Artifact Type Ambiguity Collapsing Governance

An artifact that is实质上是 an Improvement Proposal cannot be filed as a Research Artifact to avoid governance review. Type must reflect actual purpose, not desired governance treatment. If an artifact describes a gap and proposes a specific change, it is an Improvement Proposal regardless of what it is named.

### F3 — Skipping Lifecycle States

An artifact cannot move from `drafted` directly to `approved` without going through `surfaced` and `reviewed`. The lifecycle states are the gate infrastructure; skipping them bypasses the governance preparation step.

### F4 — Comparison Without Persistent References

A comparison that is not recorded — that exists only in a transient response — is not a Comparison Artifact. Comparison requires persistent artifact creation with reference to the options compared. In-memory comparisons are not valid governance inputs.

### F5 — Artifact Mutation Without Lineage

Modifying an artifact after it has been `surfaced` (not in `drafted`) must create a new artifact with a `parent_artifact_id` reference. The original artifact is `superseded`, not modified. This preserves the traceable history.

### F6 — Proposal Fragmentation Without Normalization

Existing proposal schemas (InsightProposalPayload, ChangeProposal, improvement_engine dict, self_eval dict) must normalize to Improvement Proposal type when entering governance. Proliferating proposal formats without a normalization layer violates the type contract.

### F7 — Governance Bypass Through "Internal" Classification

No artifact may be exempted from lifecycle requirements by calling it an "internal system artifact." All artifacts follow the same lifecycle rules regardless of who generated them or for what purpose.

---

## SECTION 10 — RECOMMENDED FIRST IMPLEMENTATION

### Decision: Standardize Type Field + Lifecycle State Field First

**Rationale:** Artifact types and lifecycle states are the smallest safe structural implementation. They create a shared contract that all artifact-producing systems can converge on, without changing any existing artifact-generating code.

This is the correct first step because:
1. **Additive only** — existing artifacts do not break; existing code does not change behavior
2. **Enables future convergence** — when proposal generators are next improved, they can emit the type and state fields
3. **Supports governance** — SatUi can start surfacing artifacts by type and state without requiring all artifacts to be stored yet
4. **Bounded** — type and state are just two fields; schema is minimal and well-defined
5. **Testable** — existing artifact-generating code can be checked for type/state field presence; absence is valid for backward compatibility

### What to Implement

**Step 1: Define the canonical type and state field names**

Every artifact should have:
```json
{
  "artifact_type": "research" | "analysis" | "improvement_proposal" | "comparison" | "judgment" | "continuity",
  "artifact_state": "drafted" | "surfaced" | "reviewed" | "refined" | "approved" | "denied" | "applied" | "superseded" | "archived"
}
```

**Step 2: Instrument new artifact-generating code**

When any new artifact is created, it must be created with `artifact_type` and `artifact_state` populated. The state always starts at `drafted`.

**Step 3: Instrument existing artifact-generating code (opportunistic, not mandatory)**

When existing code is touched for other reasons, add the fields. Do not refactor existing code solely for this purpose.

**Step 4: SatUi reads type and state**

SatUi surface uses `artifact_type` to determine how to display an artifact (Improvement Proposals surfaced prominently; Research Artifacts available in background). Uses `artifact_state` to determine visibility and interaction options.

**What NOT to implement first:**
- Moving all existing artifacts to the new schema (backward compatibility is valid)
- Normalizing existing proposal schemas (defer until proposal generators are next updated)
- Lifecycle automation (state transitions driven by system events — defer until the type/state foundation exists)
- Full artifact store (defer; the type/state fields can exist in memory or in existing storage)

### Implementation Order

1. Define canonical field names and document them (this document update)
2. Instrument `dialogue.py` artifact creation (research memo generation) with type + state fields
3. Instrument `self_improvement_proposal.py` with type + state fields (existing proposal creation)
4. Instrument `cross_session_artifact_eval.py` with type (`analysis`) + state fields
5. SatUi reads and displays by type and state (advisory panel for Improvement Proposals in `surfaced` state; comparison viewer for Comparison Artifacts)

This establishes the contract before any automation or schema migration.

---

## SECTION 11 — STOP LINE

- Documentation only ✅
- No code changes ✅
- No behavior changes ✅
- No routing changes ✅
- No scoring changes ✅
- No governance changes ✅
- Additive only ✅

**Files changed:**
- `docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md` — created (this document)

**Relation to existing doctrine:**
- Brick 4 (Artifact-First Evolution Principle) → extended with explicit type taxonomy and lifecycle states
- SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md → type definitions align with existing core objects (Artifact, Comparison, Judgment); lifecycle adds governance state machine
- CONTINUITY_CONTAMINATION_CONTROL_V1.md → Analysis Artifact type captures eval artifact purpose; contamination metadata attaches to Continuity Artifact
- TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md → Continuity Artifact type formalizes; lineage transitions defined
- WESLR_CANONICAL_SELF_MODEL_V1.md → type taxonomy provides consolidation target for 5 parallel proposal systems

---

*ARTIFACT_TYPES_AND_LIFECYCLE_V1 — Design Specification*
*Design only. No code. No behavior changes.*