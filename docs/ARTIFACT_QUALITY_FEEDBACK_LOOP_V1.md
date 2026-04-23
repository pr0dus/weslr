# ARTIFACT_QUALITY_FEEDBACK_LOOP_V1.md

**Version:** 1.0  
**Type:** Design Document  
**Status:** SEALED — Operator-Authored Design Intent  
**Scope:** Artifact generation → quality metadata → satellite UI → optional bridge escalation  
**Constraint:** Documentation only. No production code changes. No behavior changes.

---

## SECTION 1 — PURPOSE

### Why artifact generation should include quality feedback

When WESLR generates an artifact — a module, a research note, a governance review, a plan — it produces an output without systematic self-evaluation attached. The artifact exists. The judgment about its own quality does not. This is a gap: WESLR cannot see the difference between what it produced and what it produced well.

Quality feedback at generation time closes this gap. It does not change the artifact. It does not improve the artifact. It records what WESLR believes about the artifact's own quality, completeness, and readiness — at the moment of creation.

This is valuable for three reasons:

1. **Self-knowledge at the point of action.** The generation moment is when WESLR has the most context about why something was written a certain way. Capturing that context immediately — rather than reconstructing it later — produces more accurate quality signals.

2. **Weakness visibility.** Quality feedback makes structural weaknesses legible: thin substance, unresolved framing, missing validation paths, unclear target user. These are the same signals that would later trigger a bridge escalation. Surfacing them at generation time creates a direct path for WESLR to observe its own output limitations.

3. **Traceability.** Linking a quality assessment to an artifact at creation time creates an immutable record of what WESLR believed at that moment. This is different from post-hoc evaluation — it is the internal voice speaking before the output is shared or refined.

### Why this helps WESLR see its own weaknesses

The canonical self-model already contains the capability for self-assessment. What it lacks is a persistent, traceable connection between what WESLR produces and what WESLR thinks about what it produces.

The feedback loop makes this connection explicit and visible. WESLR does not just output artifacts — it outputs artifacts with an honest account of their limitations. Over time, this creates a record of where WESLR tends to be overconfident, where it underestimates substance gaps, and where its self-assessments diverge from operator reality.

This is not automatic improvement. It is structured self-observation.

### Why this is not the same as automatic self-improvement

Automatic self-improvement would mean: WESLR generates an artifact, detects a weakness, modifies itself or its output without operator review. That is not what this design does.

This design is:

- **Observational only at generation time.** The quality metadata is attached to the artifact. Nothing is modified. No state is changed. No proposal is generated.
- **Operator-mediated for escalation.** If the quality metadata indicates an escalation candidate, it is exposed as a preview in the satellite UI. Only an operator or operator-proxy may confirm it. The canonical bridge path is unchanged.
- **Gated by existing governance.** All escalation routes through the existing Surface-to-Spine Bridge v1, which already requires `--confirm` and explicit operator action. No new execution gates are created.

The distinction is architectural: observation plus optional human-triggered action, not autonomous modification.

---

## SECTION 2 — OPERATOR-PROXY MODE

### Defining OC Coder as temporary operator proxy

OC Coder (OpenClaw Coder) may act as a temporary operator proxy for development and testing of this loop. This means OC Coder may:

- Review quality feedback metadata attached to an artifact
- Evaluate whether an artifact represents a genuine escalation candidate
- Confirm or reject bridge previews on behalf of the operator during development sessions
- Report results of confirm/reject decisions back to the operator
- Propose adjustments to quality evaluation criteria based on observed behavior

### What OC Coder may confirm/reject in proxy mode

OC Coder in proxy mode operates within the same constraints as the canonical bridge:

- OC Coder may confirm a bridge preview that has been generated and reviewed
- OC Coder may reject a bridge preview and record the rejection
- OC Coder may not auto-confirm, auto-escalate, or bypass the preview step
- OC Coder may not modify the artifact quality evaluation criteria without operator review
- OC Coder may not record inadequacy events outside the confirmed bridge path

### What remains forbidden even in proxy mode

**Absolute prohibitions, non-negotiable even in proxy mode:**

1. OC Coder may not confirm a bridge preview without displaying the full preview output first
2. OC Coder may not suppress, hide, or delay the urgency_note when displaying a preview
3. OC Coder may not modify `requires_approval: True` on any suggestion
4. OC Coder may not route artifact quality signals directly to `record_inadequacy_event()` without going through the bridge preview path
5. OC Coder may not use artifact quality feedback as a mechanism for autonomous self-modification
6. OC Coder may not represent a rejected escalation as confirmed
7. OC Coder may not confirm escalations in bulk without per-artifact review

Proxy mode is a development convenience. It does not change the governance contract.

---

## SECTION 3 — LOOP FLOW

### The Artifact Quality Feedback Loop

```
┌─────────────────────────────────────────────────────────────────┐
│  ARTIFACT GENERATION                                             │
│  WESLR produces an artifact (module, note, plan, review)        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  QUALITY EVALUATION                                              │
│  Attached metadata generated:                                     │
│    - quality_summary (informational)                            │
│    - weakness_summary (informational)                           │
│    - proof_summary (informational)                              │
│    - escalation_readiness: {candidate, reason, urgency}         │
│    - recommended_next_action (informational)                     │
│                                                                 │
│  This evaluation is the internal voice — not a proposal,        │
│  not a routing decision, not a state change.                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  ARTIFACT STORAGE WITH ATTACHED METADATA                         │
│  Artifact written to disk with quality metadata in .meta.json   │
│  Nothing is sent to the spine. Nothing is escalated.            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  SATELLITE / UI SURFACE                                          │
│  Operator (or OC Coder in dev) sees:                             │
│    - What the artifact is                                        │
│    - What WESLR assessed about its quality                       │
│    - What WESLR identified as the main weakness                  │
│    - Whether this is an escalation candidate                     │
│    - What action WESLR recommends                                 │
│                                                                 │
│  This is observational. No action required.                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  OPTIONAL BRIDGE PREVIEW                                         │
│  If escalation_readiness.candidate == true:                      │
│    Expose bridge preview in satellite UI:                        │
│      - Signal ID, artifact ID, title                             │
│      - Urgency (with urgency_note if lowered)                    │
│      - Weakness summary                                          │
│      - Recommended next action                                   │
│      - Confirm command:                                          │
│        weslr spine bridge --from-artifact <id> --confirm         │
│                                                                 │
│  NO AUTOMATIC CONFIRM. Operator or OC Coder reviews.             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  OPERATOR-PROXY CONFIRM / REJECT                                 │
│  If confirmed:                                                   │
│    weslr spine bridge --from-artifact <id> --confirm             │
│    → Step 1: record_inadequacy_event()                           │
│    → Canonical spine processing begins                            │
│                                                                 │
│  If rejected:                                                    │
│    → Logged as rejected, artifact remains                        │
│    → No spine processing                                         │
│    → Feedback recorded for evaluation criteria review            │
└─────────────────────────────────────────────────────────────────┘
```

### What is NOT in this loop

- No direct write to `record_inadequacy_event()` from generation time
- No automatic urgency escalation without operator-proxy review
- No modification of artifact after quality evaluation
- No second parallel improvement loop
- No silent confirmations

---

## SECTION 4 — ALLOWED ATTACHED METADATA

### Fields that may be attached at generation time

These fields are informational only unless marked as escalation-related. They are attached to the artifact's `.meta.json` at creation time.

#### Informational fields

**`quality_summary: str`**
A plain-language assessment of the artifact's overall quality. One to three sentences. Describes what the artifact does well and what its general condition is. Example: *"Solid structural framing but thin on substance. Deployment steps are implied rather than explicit. Target user is clear."*

**`weakness_summary: str`**
A plain-language account of the artifact's main weaknesses as understood at generation time. Not a proposal — just a self-assessment. Example: *"No concrete examples of the optimization patterns described. Bundle structure is inferred but not shown."*

**`proof_summary: dict`**
A snapshot of proof signals at generation time:
```python
{
    "human_approvals": 0,       # none at creation
    "handoff_acceptances": 0,   # none at creation
    "real_usage_hits": 0,       # none at creation
    "external_validation_state": "unvalidated"
}
```

**`recommended_next_action: str`**
What WESLR recommends doing with this artifact next. This is advisory only. Examples: *"Run validate/accept to test in a trial", "Add concrete examples before promoting", "Hand off to another agent for review."*

#### Escalation-related fields

**`escalation_readiness: dict`**
This field indicates whether the artifact is a candidate for bridge escalation. It does not trigger escalation — it surfaces it for operator review.

```python
{
    "candidate": bool,          # True if this artifact has escalation potential
    "reason": str,              # Why WESLR thinks this should be reviewed
    "urgency": str,            # "low" | "medium" | "high"
    "urgency_note": str,       # Why urgency was assessed this way (informational)
    "bridge_preview_shown": bool,  # Has the operator seen the preview?
    "bridge_confirmed": bool | None  # None = not reviewed, True = confirmed, False = rejected
}
```

**`bridge_candidate_preview: dict | None`**
Populated only when `escalation_readiness.candidate == True`. This is the same preview data that would be shown in the satellite UI.

```python
{
    "signal_id": str,           # bridge_xxxxxxxx
    "artifact_id": str,
    "artifact_title": str,
    "urgency": str,
    "urgency_note": str,
    "runtime_state": str,
    "category": str,
    "confidence": float,
    "weakness_summary": str,
    "recommended_next_action": str,
    "proof_summary": dict,
    "confirm_command": str      # Full CLI command for operator
}
```

### Field governance

| Field | Informational | Escalation-Related | Notes |
|-------|:---:|:---:|------|
| `quality_summary` | ✅ | | May be displayed in satellite UI |
| `weakness_summary` | ✅ | | May be displayed in satellite UI |
| `proof_summary` | ✅ | | Read-only snapshot at generation |
| `recommended_next_action` | ✅ | | Advisory only |
| `escalation_readiness` | | ✅ | Reviewed by operator |
| `bridge_candidate_preview` | | ✅ | Shown only when candidate=True |

No field may be used to directly trigger `record_inadequacy_event()`. The bridge preview path is always required.

---

## SECTION 5 — SATELLITE UI RELATION

### How this appears in artifact detail views

The satellite/UI surface should display artifact quality feedback as a distinct, readable section — not buried in metadata, not hidden behind a toggle. The goal is for an operator to open an artifact detail view and immediately understand:

1. What WESLR thinks this artifact is
2. How good WESLR believes it is
3. What WESLR sees as the main weakness
4. Whether WESLR believes this should be escalated for operator review

### Proposed layout for artifact detail view

```
══════════════════════════════════════════════════
ARTIFACT: Governance Transparency Review
ID: agent-1-governance_transparency_review-1776146241
Type: governance_document  ·  Family: governance
Created: 2026-04-13  ·  Destination: internal_review
══════════════════════════════════════════════════

WESLR SELF-ASSESSMENT

Quality:    Moderate — solid framing, weak substance
Weakness:   No concrete governance decisions documented;
            framework is described but not demonstrated
Confidence: 0.30 (low — early-stage artifact)

Proof:      Human approvals: 1  ·  Real usage: 0  ·  Handoff accepts: 0
            (proof signals from creation time snapshot)

══════════════════════════════════════════════════

ESCALATION READINESS

  [ ] This artifact shows an escalation candidate
      Reason: artifact substance looks thin relative to its framing
      Urgency: medium (lowered from high — human approval signal present)
      Next action: strengthen underlying governance artifact
                   before promoting or trading

      [Preview Bridge to Spine]
      Command: weslr spine bridge --from-artifact agent-1-... --confirm

══════════════════════════════════════════════════

OPERATOR NOTES
[free text field — operator may record decision reason]

──────────────────────────────────────────────────
[CONFIRM ESCALATION]    [REJECT]    [CANCEL]
```

### What the satellite UI must show

- `quality_summary`: one-line quality label + supporting detail
- `weakness_summary`: clear description of main weakness
- `confidence`: numeric value (context for how certain WESLR is)
- `proof_summary`: human_approvals, real_usage_hits, handoff_acceptances
- `escalation_readiness.candidate`: yes/no with reason
- `urgency` and `urgency_note`: visible when candidate is true
- `recommended_next_action`: plain-language recommendation
- Confirm/reject buttons: visible only when `candidate == True`

### What the satellite UI must NOT do

- Must not auto-confirm escalation
- Must not hide or minimize the urgency_note
- Must not display `bridge_confirmed == True` without operator action
- Must not route directly to `record_inadequacy_event()` without explicit confirm
- Must not allow bulk confirmations without per-artifact review

---

## SECTION 6 — BRIDGE RELATION

### How this loop connects to Surface-to-Spine Bridge v1

The Artifact Quality Feedback Loop does not replace, modify, or bypass the Surface-to-Spine Bridge v1. It connects to it at a single, defined point: the satellite UI preview.

```
Generation
    │
    ▼
Quality Evaluation (attached as metadata)
    │
    ▼
Artifact Storage (with quality metadata in .meta.json)
    │
    ▼
Satellite UI ← reads quality metadata
    │
    ├── escalation_readiness.candidate == False → display only, no action
    │
    └── escalation_readiness.candidate == True
              │
              ▼
         Bridge Preview exposed in UI
              │
              ├── Operator / OC Coder reviews preview
              │
              ├── CONFIRM → weslr spine bridge --from-artifact <id> --confirm
              │              │
              │              ▼
              │         Surface-to-Spine Bridge v1 (existing)
              │              │
              │              ▼
              │         Step 1: record_inadequacy_event()
              │
              └── REJECT → logged, artifact remains, no spine processing
```

### Explicit constraints on bridge connection

1. **No direct Step 1 writes at generation time.** Quality metadata is attached to the artifact. No call to `record_inadequacy_event()` is made. No bridge signal is sent. The artifact is simply stored with an honest self-assessment.

2. **Only the preview/confirm path may escalate.** An artifact does not become an escalation candidate simply because `escalation_readiness.candidate == True`. The operator must see the preview and confirm it. The `--confirm` flag on `weslr spine bridge` is always required.

3. **Urgency derivation is unchanged.** When a bridge preview is generated for an artifact, urgency is derived from the existing `_urgency_from_evaluation()` logic in `surface_to_spine_bridge.py`. The quality metadata at generation time does not pre-compute or override the urgency that will be derived at bridge preview time.

4. **No new bridge type is created.** The loop uses the existing `artifact_weakness` surface type for the `source_surface` field. No new `SURFACE_TYPE` value is needed.

5. **No routing change.** The `surface_to_spine_bridge.py` module is not modified to accept generation-time metadata as an alternative input path. The only entry point remains `preview_bridge()` and `confirm_bridge()` via CLI.

---

## SECTION 7 — FORBIDDEN DRIFT

This section enumerates specific behaviors that are prohibited under this design. These are not implementation details — they are architectural constraints. Violating any of them constitutes a governance breach, not merely a technical deviation.

### Absolute prohibitions

**1. Artifact generation may not directly mutate improvement state.**
At generation time, no call may be made to `record_inadequacy_event()`, `improve_*`, `propose_*`, or any function in the self-improvement spine. The artifact is written. The quality metadata is attached. That is all.

**2. Quality evaluation may not trigger automatic escalation.**
`escalation_readiness.candidate == True` creates a preview. It does not create a confirmation. No automatic `--confirm` may be applied. No background process may monitor new artifacts and confirm them without operator action.

**3. No second parallel self-improvement loop.**
The canonical self-improvement spine is Lane A. This loop does not create Lane B. It does not create a parallel intake path into `record_inadequacy_event()`. It does not introduce a separate governance structure for artifact-generated inadequacy signals. All artifact-generated escalation candidates route through the same Step 1 as every other surface.

**4. No silent operator-proxy confirmations.**
OC Coder in proxy mode may confirm or reject previews. All confirmations must be displayed in full before being executed. A confirmation that does not surface the preview text is not a valid confirmation.

**5. No hidden score tuning based on artifacts.**
Quality evaluation at generation time may not adjust `internal_score`, `confidence`, or any scoring parameter based on the artifact's content in a way that would make subsequent bridge evaluations of the same artifact dependent on the self-evaluation. The quality metadata is descriptive, not constitutive of the artifact's quality.

**6. OC Coder may not modify escalation criteria without operator review.**
If OC Coder, acting as operator proxy, observes that the quality evaluation criteria are generating inappropriate candidates (too many or too few), it may propose adjustments. It may not implement them without operator approval.

**7. No bulk confirmations.**
Each artifact escalation requires individual review. A confirmation action that processes multiple artifacts simultaneously without per-artifact preview display is prohibited.

**8. Proof signals in quality metadata may not be backdated.**
The `proof_summary` snapshot is taken at generation time. It reflects the proof state at that moment. Artifacts may not be retrospectively assigned proof signals to manipulate urgency at bridge preview time.

---

## SECTION 8 — RECOMMENDED FIRST IMPLEMENTATION SLICE

### Smallest safe first step

The design above is large. Implementing it all at once would be high-risk and hard to validate. The first slice should be narrow enough to be clearly bounded and well-tested.

**First slice scope:**

1. **Add `quality_summary`, `weakness_summary`, and `recommended_next_action` to artifact `.meta.json` output from the artifact generation point.**
   - These are plain string fields. No new schema. No new validation.
   - Generated by the existing `build_artifact_explainability()` or a simplified version of it.
   - Written to the artifact's `.meta.json` file at creation time.
   - **No `escalation_readiness` field in this slice.**

2. **Expose these fields in the satellite/UI artifact detail view.**
   - Read `quality_summary`, `weakness_summary`, `recommended_next_action` from `.meta.json`.
   - Display them in the artifact detail section.
   - No new actions. No confirm/reject buttons. Display only.

3. **No bridge preview. No operator action. No escalation path in this slice.**
   - This slice proves the feedback loop mechanics without changing any governance state.
   - It proves that quality metadata can be generated, stored, and displayed.
   - It does not change how escalations work.

**What this slice does NOT include:**

- No `escalation_readiness` field
- No bridge preview generation
- No changes to `surface_to_spine_bridge.py`
- No OC Coder proxy mode
- No urgency derivation changes
- No changes to `record_inadequacy_event()` call paths
- No new satellite UI confirm/reject actions

**Validation for slice 1:**

- New artifacts have `quality_summary`, `weakness_summary`, `recommended_next_action` in their `.meta.json`
- Existing artifacts (without these fields) display cleanly without these fields
- Satellite UI artifact detail view shows the new fields when present
- No changes to existing test behavior
- No new files written outside the artifact's own `.meta.json`

---

## SECTION 9 — STOP LINE

This document is a **design specification**. It authorizes no code changes. It creates no implementation obligation. It does not modify any existing module, schema, or behavior.

**Enforcement:**

- No `surface_to_spine_bridge.py` changes in this step
- No new production paths to `record_inadequacy_event()`
- No auto-confirm logic
- No OC Coder proxy mode activation
- No changes to `weslr/main.py` or CLI commands
- No new schema fields except those defined in Section 4 as informational-only

**Next step:** Operator reviews this document. If approved, implementation of Section 8 slice 1 may be authorized in a separate instruction.

---

**Document:** ARTIFACT_QUALITY_FEEDBACK_LOOP_V1.md  
**Authored:** 2026-04-21  
**Status:** SEALED — Operator Design Intent  
**Stop line active:** Yes
