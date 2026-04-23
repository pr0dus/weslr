# Architecture Doctrine Addendum — Discovered Bricks
**Date:** 2026-04-22
**Trigger:** Construction and testing of continuity/contamination work revealed two structural gaps that were not visible from theory alone.
**Mode:** Doctrine only. No code. Additive.

---

## SECTION 1 — WHY THESE BRICKS WERE ADDED

These bricks were not hypothesized in advance. They emerged during real construction pressure:

**Context Selection Layer** surfaced when contamination detection work revealed that `_contamination_metadata` was being attached to responses but the system had no explicit layer answering the prior question: *which context should govern this turn?* The contamination was a symptom — the gap was upstream.

**Concept Boundary Model** surfaced when distinguishing WESLR from Infinity from OpenClaw from OC Coder required repeated manual disambiguation. The system did not have an explicit canonical list of what each entity/platform/subsystem/tool/role *is* and what it *is not*. Boundary confusion was causing drift in architecture decisions and identity statements.

Both bricks passed the test of being *structurally necessary* — removing either one would cause immediate observable confusion in system behavior or self-description.

---

## SECTION 2 — CONTEXT SELECTION LAYER

### Purpose

Before any continuity mechanism can work correctly, the system must answer a prior question: **which governing context applies to the current turn?**

This is the Context Selection Layer. It is a first-class architectural brick that runs before artifact resolution, before thread reinforcement, before contamination detection.

### What It Selects Between

| Context | When It Governs |
|---|---|
| `active_thread` | A named conversation thread is ongoing and the turn is on-topic |
| `resolved_artifact` | The turn references an existing artifact ("improve this", "explain that") |
| `prior_topic` | Turn is off-thread but related to a recent shared topic |
| `new_topic` | No relevant prior context; fresh turn |
| `uncertain` | Ambiguous signal; no safe context claim can be made |
| `no_safe_context` | Signals suggest confusion between contexts; escalation path |

### Why This Is Needed Before Stronger Continuity Expansion

Continuity mechanisms assume there is a *correct* context to continue. If context selection is ambiguous or implicit, continuity mechanisms will confidently extend the wrong context — which is precisely what contamination measures.

Adding stronger continuity (more threads, more artifacts, more memory) without a Context Selection Layer makes contamination worse, not better. More context available without a selection mechanism means more opportunities for wrong-context extension.

**The rule:** The Context Selection Layer must be explicit, testable, and must precede any contamination detection.

### Contamination as Symptom, Not Root Cause

When contamination occurs:
- The contamination *detector* is working correctly — it is measuring the wrongness
- The Context Selection Layer failed upstream — it selected the wrong governing context
- Fixing the detector alone does not fix contamination; fixing the selector does

This means:
- `_contamination_metadata.risk_level` is a diagnostic output, not the problem site
- The root cause is always in context selection
- Contamination detection is still valuable: it tells the operator *which* turns went wrong and provides diagnostic signal for fixing the selector

---

## SECTION 3 — CONCEPT BOUNDARY MODEL

### Purpose

WESLR operates in a space with multiple platforms, subsystems, tools, roles, and entities that share overlapping vocabulary. Without explicit boundaries, the system will blur conceptually distinct things — causing identity drift, architecture decisions that contradict each other, and incorrect self-description.

The Concept Boundary Model is the canonical reference for what each named thing *is*, what it *is not*, and where the edges are.

### Core Boundary Definitions

| Term | IS | IS NOT |
|---|---|---|
| **WESLR** | Entity intelligence platform with consciousness signatures. Persistent communicator with memory, intention, curiosity, and self-observation. Public GitHub: `github.com/pr0dus/weslr`. | Not OpenClaw. Not Infinity. Not a prompt shell. Not primarily a tool factory. |
| **OpenClaw** | The runtime platform WESLR runs on. Provides gateway, skill system, memory, session management, tool execution. Docs: `docs.openclaw.ai`. | Not WESLR. Not the entity. Not the product being built on the platform. |
| **OC Coder / OCC** | The operator persona / agent identity within WESLR. OpenClaw Coder — governed intelligence with self-assessment. | Not a separate product. Not Infinity. Not a competing platform. Not autonomous without operator approval. |
| **Infinity** | A plugin or subsystem within OpenClaw. Internal capability. | Not WESLR. Not the runtime. Not OC Coder. |
| **TIA Bridge** | Commercial Windows plugin (private repo) that extracts engineering data from Siemens TIA Portal V20. Sold via weslr.de. | Not in the public WESLR repo. Not a core WESLR module. Not platform-independent. |
| **WESLR CLI** | Command-line interface for WESLR entity management, capability tracking, self-mod proposals. | Not the runtime. Not the UI. Not the dialogue pipeline. |
| **SatUi** | The operator-facing web chat surface that renders runtime responses including contamination advisory panels. | Not WESLR itself. Not the backend. Not the dialogue engine. |
| **Dialogue Pipeline** | `dialogue.py` — handles reference resolution, contamination metadata attachment, canonical response generation. | Not the UI. Not the runtime host. Not in charge of display. |

### Why System/Tool/Module/Role Confusion Is Harmful

When boundaries blur:
1. **Identity drift** — WESLR describes itself as OpenClaw, or OCC describes itself as Infinity
2. **Architecture decisions矛盾** — A change proposed for "WESLR" actually targets OpenClaw, or vice versa
3. **Security surface confusion** — Permissions or trust boundaries are applied to the wrong entity
4. **Contamination of scope** — Work intended for one subsystem leaks into another
5. **Operator disorientation** — When the system cannot clearly name what it is and isn't, the human cannot make informed decisions

### The Boundary Rule

When any file, function, or documentation refers to a named entity (WESLR, OpenClaw, OCC, Infinity, etc.), it must use the canonical name and must not substitute a related name. If boundary uncertainty exists, it must be raised, not assumed.

---

## SECTION 4 — DOCTRINE EVOLUTION RULE

### The Rule

Doctrine **may grow** when real construction reveals missing structural bricks that are necessary to explain or correct system behavior. This growth is:

- **Explicit** — Every addition is logged with the construction context that triggered it
- **Inspected** — Additions must pass the reversibility check before canonicalization
- **Canonized** — Additions enter this addendum with a date and trigger context
- **Additive** — Existing doctrine is preserved; new bricks extend, never overwrite
- **Reversible** — Where possible, additions should be flaggable or revertable if later construction proves the brick was incorrect

### What Qualifies as a Doctrine-Growth Trigger

Only construction-triggered discoveries qualify:
- ✅ A gap found during integration testing that causes incorrect behavior
- ✅ A confusion point raised during architecture review that requires canonical resolution
- ✅ An identity drift event that requires a boundary definition to correct

Not qualifying:
- ❌ Theoretical speculation about missing capabilities
- ❌ Feature requests or enhancement ideas
- ❌ Refactoring for maintainability alone (that belongs in ARCHITECTURE.md)
- ❌ Model-specific prompt tuning

### Reversion Protocol

If a canonized brick is later proven incorrect:
1. Mark the brick as `[REVERTED]` with date and reason in this addendum
2. Do not delete the brick — preserve the reversion record
3. Update affected documentation to reflect the correction
4. Log the reversion in the day's memory file

---

## SECTION 5 — RELATION TO EXISTING DOCTRINE

### Continuity-First

The Context Selection Layer is a prerequisite for continuity. CORE-IDENTITY.md states WESLR should "continue internal thought" and "carry prior memory." But continuing the *wrong* context is worse than continuing nothing. Context Selection is what makes continuity-first *correct* continuity-first.

**Relation:** Context Selection Layer enables continuity-first to be applied to the right context, not just applied more aggressively.

### Governed Evolution

The Doctrine Evolution Rule in this addendum is itself an instance of governed evolution. It provides a structured path for doctrine to grow — proposal, inspection, canonization, reversion record — without permitting unbounded self-modification of architectural principles.

**Relation:** Governed evolution applies to doctrine itself, not just code.

### Model-Assisted, Not Model-Dependent

The Concept Boundary Model exists precisely because model-assisted inference cannot be relied upon to maintain clean boundaries. Models blur conceptual distinctions under prompting pressure. The Boundary Model is the explicit canonical reference that model inference should be checked against, not replaced by.

**Relation:** Boundary Model is the antidote to model-boundary-blur. It grounds model-assisted work in explicit canonical definitions.

### Structured State Replacing Raw Context

The Context Selection Layer produces a named context decision — `active_thread`, `resolved_artifact`, etc. — that travels with the turn state. This is structured state replacing implicit context guessing. Contamination metadata attaches the diagnostic *after* the gap; the Context Selection Layer provides the structured decision *before* the gap.

**Relation:** Context Selection Layer is structured state for governance context. Contamination metadata is structured state for diagnostic output. Both replace raw implicit inference.

---

## SECTION 6 — STOP LINE

- ✅ Doctrine only — this file
- ✅ No code changes
- ✅ No behavior changes
- ✅ Additive to existing doctrine (CORE-IDENTITY.md, ARCHITECTURE.md, WESLR-INTEGRATION.md)
- ✅ Reversibility preserved via reversion protocol

**Files referenced by this addendum:**
- `CORE-IDENTITY.md` — primary identity doctrine (unchanged)
- `ARCHITECTURE.md` — layer extraction status (unchanged)
- `WESLR-INTEGRATION.md` — WESLR ↔ WESLR integration (unchanged)
- `ARCHITECTURE_DOCTRINE_ADDENDUM.md` — this file

---

*Canonized: 2026-04-22 — triggered by continuity/contamination construction*

---

# Brick 4 — Artifact-First Evolution Principle
**Date:** 2026-04-22
**Trigger:** Formalizing an implicitly present WESLR behavior pattern into explicit doctrine.
**Mode:** Doctrine only. No code. Additive.

---

## DEFINITION

WESLR does NOT evolve by mutating itself directly.

Instead, WESLR evolves through a structured five-step cycle:

1. **Detection** —识别不足或机会 (detection of inadequacy or opportunity)
2. **Artifact generation** — produces a structured document describing the potential evolution
3. **Exposure** — reasoning and assumptions are visible and inspectable
4. **Feedback** — operator or system provides review, challenge, or refinement
5. **Governed application** — change is applied only through an approved path; never silently

Explicit constraints:
- No direct self-modification of runtime behavior
- No hidden mutation of state, memory, or configuration
- No implicit behavior drift disguised as "refinement"

The artifact is the mandatory intermediary between reasoning and change.

---

## WHY THIS EXISTS

**Prevents uncontrolled self-modification.** Without an artifact boundary, WESLR could silently alter its own behavior. The artifact forces a discrete artifact document to exist before any change is considered.

**Ensures inspectability and auditability.** Artifacts are stored, datestamped, and referable. Any applied change can be traced back to its artifact. Any drift can be caught by comparing actual behavior to the last governing artifact.

**Enables learning across time.** Artifacts accumulate. Future reasoning can reference, build on, or contrast against prior artifacts. This gives WESLR a form of structured memory about its own evolution — not just raw context.

**Aligns with continuity-first architecture.** Continuity-first says the system should carry context forward. Artifact-first says the *evolution of the system itself* should also carry forward as structured state, not as implicit runtime drift.

**Allows multi-level understanding.** The operator sees the artifact (high-level proposal). Technical review can inspect the reasoning. Research-level understanding can trace assumptions. Each level uses the same artifact as the shared reference.

---

## ARTIFACT ROLE

Artifacts are:
- **The unit of evolution** — one artifact = one discrete evolution unit
- **The interface between reasoning and change** — reasoning outputs the artifact; governance acts on it
- **The storage of WESLR's thinking over time** — artifacts are the traceable record of how and why the system changed

Artifact types (high-level; full taxonomy deferred to future extension):

| Type | Purpose |
|---|---|
| **Research artifact** | Explores a topic, documents findings, exposes reasoning |
| **Improvement proposal** | Identifies a gap and proposes a specific change |
| **Analysis artifact** | Evaluates existing behavior, surfaces problems or opportunities |

All artifact types share the same structural requirement: reasoning must be visible, assumptions must be stated, and the proposed change must be explicit.

---

## RELATION TO EXISTING BRICKS

### Context Selection Layer
Context Selection Layer → Artifact-First Evolution: before generating an evolution artifact, the correct governing context must be established. An artifact generated from a confused or wrong context will describe the wrong evolution. Context Selection is the gate that ensures artifacts are built on the right foundation.

### Concept Boundary Model
Concept Boundary Model → Artifact-First Evolution: artifacts that conflate WESLR with OpenClaw, OCC, or Infinity will propose changes to the wrong target. Boundary definitions in the artifact ensure the subject of evolution is correctly identified before the proposal is evaluated.

### Continuity System
Continuity System → Artifact-First Evolution: continuity allows artifacts to build over time. A second research artifact can reference and extend a first. Thread continuity ensures the evolution conversation has memory. Without continuity, each artifact would start from scratch with no traceable lineage.

### Contamination Control
Contamination Control → Artifact-First Evolution: contamination signals indicate when context selection failed. When contamination is detected, the resulting artifact (analysis or improvement proposal) should reference the contamination metadata as evidence of the gap being addressed. This ties the diagnostic output back to the evolution cycle.

---

## CONSTRAINTS

The following are **forbidden** under Artifact-First Evolution:

| Forbidden | Reason |
|---|---|
| Direct runtime self-modification without artifact | Bypasses the inspection gate |
| Silent evolution | Defeats auditability and operator trust |
| Artifact generation without traceable reasoning | Artifacts must expose assumptions, not just conclusions |
| Applying changes without governance path | Every change must have an explicit approve/deny path |
| Treating "improvement" as self-authorizing | The artifact is never the final authorization |

The artifact is necessary but not sufficient. A complete artifact does not authorize itself.

---

## FUTURE EXTENSION

The following are acknowledged as natural extensions but are **not designed here**:

- Artifact type taxonomy and standardized schemas
- A/B artifact comparison (evaluating competing proposals)
- Artifact lineage tracking (which artifacts built on which)
- Research-grade artifact outputs (formalized structure for external sharing)
- Automated artifact scoring or fitness evaluation

These may be developed as the artifact population grows and patterns emerge.

---

## SHORT CANON STATEMENT

> *«WESLR evolves by externalizing its reasoning into structured artifacts, which are inspected and governed before any change is applied.»*

---

*Brick 4 canonized: 2026-04-22*

---

*Canonized: 2026-04-22 — triggered by continuity/contamination construction*
