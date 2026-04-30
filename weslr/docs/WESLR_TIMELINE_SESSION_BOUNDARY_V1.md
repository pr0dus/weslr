# WESLR TIMELINE VS SESSION BOUNDARY V1

**Version:** 1.0
**Status:** SPEC ONLY — does not affect runtime
**Date:** 2026-04-30

---

## 1 — Core Definitions

### Session

A **session** is a bounded interaction window. It:
- Has a `session_id`
- Contains messages, responses, and signals produced during the window
- Is resettable; state does not persist beyond the session boundary by default
- Is used for local interaction analysis, ephemeral follow-up, and short-term signal collection

A session does NOT imply long-term memory, stability determination, or value inference.

### Timeline

A **timeline** is an ordered record of events across time. It:
- Spans sessions and runs
- Is used for continuity, provenance, stability assessment, and review
- Records what happened, in order, across multiple sessions
- Is not the same as chat memory or transcript storage

A timeline does NOT expose public internals, bypass governance, or act as behavior memory.

---

## 2 — When To Use Session

Use session for:

- One conversation run
- One observation run
- Ephemeral continuity within a turn or short exchange
- Short-term follow-up resolution
- Local signal collection

Session must NOT:
- Imply long-term memory
- Determine value stability alone
- Overwrite timeline truth
- Serve as the basis for review-readiness

---

## 3 — When To Use Timeline

Use timeline for:

- Cross-run ordering of events
- Temporal stability assessment
- Provenance chains
- Review decision history
- Pressure pattern persistence tracking
- Operator consistency analysis

Timeline must NOT:
- Become raw chat transcript storage
- Expose public internals or intermediate signals
- Bypass governance boundaries
- Act as a behavior memory or preference store

---

## 4 — Relationship

```
message → session event → signal → pattern → timeline position → review
```

**Session produces events. Timeline orders events. Patterns are compared across timeline. Operator reviews timeline-backed evidence.**

- A session generates signal observations
- Signal observations are mapped to patterns
- Patterns are ordered on the timeline with provenance references
- Review operates on timeline-backed evidence, not session-only observations
- Stability assessment uses timeline ordering, not session-internal state

Session data feeds into timeline records. Timeline records do not feed back into session behavior.

---

## 5 — Observation Environment

Each observation session:
- Has a unique `session_id`
- Produces signal observations local to that session

Each observation batch (across multiple sessions):
- Creates timeline segments
- Is used only after observation runs complete
- Supports stability assessment only after multi-session evidence is collected

Single-session observation is insufficient for review-readiness. This is consistent with WESLR_VALUE_STABILITY_CRITERIA_V1 Gate G5 (`total_runs >= 3`).

---

## 6 — Ephemeral Continuity

Ephemeral continuity belongs to the session only. It expires after one turn or one session.

Ephemeral observations must NOT be written to the timeline unless explicitly logged as an observation signal with proper provenance.

The boundary:
```
Ephemeral (session-scoped) → must not persist to timeline
Explicitly logged signal → may enter timeline record
```

Ephemeral state is not stability evidence. Only logged, provenance-traced signals contribute to timeline-based review.

---

## 7 — Value / Emergence Layer

Value stability requires timeline evidence. Sessions alone are insufficient for review-readiness.

Review-readiness requires:
- Multiple sessions
- Ordered timeline evidence
- Traceable provenance from signal to pattern to decision

This aligns with WESLR_VALUE_STABILITY_CRITERIA_V1 thresholds: `total_runs >= 3`, `run_diversity >= 2`, and traceable provenance.

The emergence layer does not use session memory. It uses timeline records with documented provenance chains.

---

## 8 — Public Mode

Public users see neither session internals nor timeline internals.

Public output must remain natural — structured from normal WESLR response layers, not from internal observation or review state.

Public-facing behavior is governed by WESLR public readiness architecture. Timeline and session internals are not surfaced in public output under any circumstances.

---

## 9 — Prompt / Runtime Adaptation Rule

Do NOT adapt WESLR's public prompt based on timeline or session data.

### Allowed

- Operator-internal analysis
- Review reports and diagnostics
- Consistency layer analysis (WESLR_OPERATOR_CONSISTENCY_LAYER_V1)
- Structured operator tooling

### Forbidden

- Changing public chat tone based on timeline history
- Hidden personalization driven by session data
- Silent prompt mutation from operator review output
- Session-to-session behavior drift in public responses
- Any modification of public-facing prompts from internal observation

This rule applies regardless of whether adaptation would improve user experience. The mechanism is forbidden, not the outcome.

---

## 10 — What Does NOT Need Prompt Adaptation

No prompt adaptation required for:

- Deterministic handlers
- Graph traversal logic
- Evidence overlays
- Pressure observation
- Stability review
- Operator consistency diagnostics

These use structured state and rule-based logic, not prompt memory. They do not read session or timeline data to determine behavior.

The absence of prompt adaptation for these layers is intentional, not a gap.

---

## 11 — Future Use

Future prompt adaptation, if ever considered, requires:

- A separate, explicit doctrine document
- Operator approval with documented rationale
- Traceable change with rollback plan
- Public documentation of the adaptation scope

Until such a doctrine exists and is approved, no prompt adaptation is authorized under any circumstances.

---

## 12 — Verdict

```
WESLR_TIMELINE_SESSION_BOUNDARY_DEFINED
```

Key distinctions:
- **Session** = bounded, resettable, local signal collection
- **Timeline** = ordered, cross-run, provenance-backed evidence record
- **Session produces; timeline orders; review operates on timeline**
- **No prompt adaptation from session or timeline data**
- **Public output remains natural regardless of internal state**

---

*Spec version 1.0 — does not affect runtime behavior*
*Validation: run independently; no behavioral assertions in this spec*