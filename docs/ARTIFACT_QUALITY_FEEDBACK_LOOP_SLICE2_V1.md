# ARTIFACT_QUALITY_FEEDBACK_LOOP_SLICE2_V1.md

**Version:** 1.0  
**Type:** Design Document  
**Status:** SEALED — Operator-Authored Design Intent  
**Scope:** Bridge candidate preview for informational escalation candidacy in artifact detail views  
**Prerequisite:** ARTIFACT_QUALITY_FEEDBACK_LOOP_V1.md (Slice 1) — implemented  
**Constraint:** Documentation only. No production code changes. No behavior changes.

---

## SECTION 1 — PURPOSE

### Why Slice 1 informational feedback is not enough

Slice 1 proved that WESLR can honestly assess its own artifact at generation time and record that assessment as metadata. The `quality_feedback` block — `quality_summary`, `weakness_summary`, `recommended_next_action`, `proof_summary` — is now written to disk and visible in the satellite UI. The operator can see what WESLR thought about the artifact when it was created.

But Slice 1 has a ceiling. It is purely observational: the quality feedback exists, but nothing connects it to a possible escalation action. The operator who sees a thin artifact in the satellite UI has no path from that observation to a bridge confirmation without manually running the bridge CLI themselves. The loop is open on both ends — generation produces feedback, but the feedback goes nowhere actionable.

This is the right behavior for Slice 1. It proved the mechanism without introducing any escalation risk. But it means the quality feedback loop, as currently implemented, cannot serve as a real escalation input to the self-improvement spine.

### Why bridge candidate preview is the next safe step

The next safe step is not escalation. It is *visibility of escalation candidacy*.

If an artifact's `quality_feedback` indicates a structural weakness — thin substance, recurring limitation signal, high deployment friction with no external proof — the satellite UI should show the operator that this artifact has escalated-significance potential. It should do this without triggering any confirmation, without creating a bridge object, without writing to any spine state, and without any new execution path.

The preview data tells the operator: *this artifact looks like a bridge candidate based on its quality signals; here is the urgency and the reason; here is the command you would run if you wanted to confirm it.*

This is the smallest next step because:

1. **It uses existing data.** The urgency and risk signals already exist in `build_artifact_explainability()`. No new scoring, no new detection logic.
2. **It reuses the existing bridge surface type.** `artifact_weakness` is already a valid `SURFACE_TYPE` in the canonical bridge.
3. **It is purely informational.** No confirmation, no Step 1 write, no governance change.
4. **It creates the visible path.** The operator sees the feedback and sees the escalation option. The loop is now closed at the display layer, not the execution layer.

---

## SECTION 2 — RELATION TO EXISTING BRIDGE

### Slice 2 reuses the existing `artifact_weakness` bridge path

The Surface-to-Spine Bridge v1 already supports `source_surface = "artifact_weakness"` and implements `preview_bridge()` and `confirm_bridge()`. Slice 2 does not create a new bridge type. It does not create a new entry point to `record_inadequacy_event()`. It does not modify `surface_to_spine_bridge.py`.

What Slice 2 does: it surfaces the *candidate data* — what the bridge would look like if invoked — inside the existing artifact detail views. This is a presentation-layer addition. The actual escalation path remains exactly `weslr spine bridge --from-artifact <id> --confirm`.

### No second escalation system

There is one canonical escalation path from artifact weakness to the self-improvement spine:

```
artifact weakness → surface_to_spine_bridge → record_inadequacy_event() → canonical spine
```

Slice 2 does not create:

- A second bridge module
- A parallel entry to `record_inadequacy_event()`
- A new `SURFACE_TYPE` value
- A new CLI command
- A CDI trigger
- A new proposal schema

The `bridge_candidate_preview` is a *read-only projection* of what the canonical bridge would produce. It cannot write to the spine. It cannot confirm itself. It exists solely to inform the operator's decision.

---

## SECTION 3 — ELIGIBILITY RULES

### When quality feedback may produce a bridge candidate preview

An artifact qualifies for a `bridge_candidate_preview` when its `quality_feedback` indicates elevated risk beyond a minimum threshold. The rules are derived entirely from signals already produced by `build_artifact_explainability()`. No new scoring, no new detection, no new thresholds.

**Eligible when urgency is `medium` or `high`** — as derived from the existing urgency derivation logic (Section 3 of `SURFACE_TO_SPINE_BRIDGE_V1.md`):

- **High urgency** — recurring limitation signal present (risk text contains "thin", "substance", or "rejected"), OR multiple concurrent risk flags
- **Medium urgency** — no recurring limitation, but weak external proof combined with elevated deployment friction or low buyer clarity

**AND at least one of the following weakness indicators** is present:

1. `weakness_summary` contains "thin", "substance", "weak external proof", "deployment effort", "rejected", or "low clarity" — indicating a substantive gap, not just a generic note
2. `proof_summary.human_approvals == 0` AND `proof_summary.real_usage_hits == 0` AND `proof_summary.handoff_acceptances == 0` — indicating no external proof
3. `quality_summary` contains "early-stage" or "substance still forming" — indicating an immature artifact being promoted

### What is NOT enough on its own

The following conditions, individually, are **not sufficient** to produce a bridge candidate preview:

| Condition | Why insufficient alone |
|-----------|----------------------|
| `quality_summary` = "decent internal quality" | Good internal score without external proof is not a structural weakness |
| `proof_summary.human_approvals >= 1` | Human approval is itself a proof signal; further escalation may not be needed |
| Artifact is old / many state refreshes | Age is not a weakness signal; the artifact may be genuinely solid |
| Artifact has been exported | Prior export is evidence of value; not a weakness indicator |
| `recommended_next_action` = "continue validation" | No specific weakness identified; no escalation warranted |
| Urgency = `low` | Already below the escalation threshold; preview would add noise without signal |

### Explicitly excluded artifact states

A `bridge_candidate_preview` is **never** produced when:

- `review_status` is `approved` or `export_ready` — artifact has operator validation
- `lifecycle_stage` is `packed` or `deployed` — artifact has progressed beyond escalation range
- `proof_summary.human_approvals >= 1` AND urgency is `low` or `medium` — human approval already addressed the concern
- A `bridge_confirmed` timestamp already exists on the artifact — escalation already occurred

---

## SECTION 4 — PREVIEW OBJECT SHAPE

### Metadata shape for bridge candidate preview

The `bridge_candidate_preview` is a read-only informational dict. It is **not** a `SurfaceBridgeObject`. It is not passed to any bridge function. It is not written to any spine state. It exists only in the artifact detail payload.

```python
bridge_candidate_preview: {
    # Classification
    "candidate": bool,                    # Always True when preview is present
    "surface_type": "artifact_weakness",  # Matches existing SURFACE_TYPE in bridge v1
    "spine_target": "step1_inadequacy_signal",  # Canonical target step

    # Urgency
    "urgency": str,                        # "medium" or "high" — from urgency derivation
    "urgency_note": str,                   # Why urgency was assessed this way

    # Why this is a candidate
    "confidence": float,                   # Estimated confidence (0.0–1.0)
    "why": List[str],                     # Summarized weakness indicators (1–3 items)

    # Operator guidance
    "recommended_action": str,            # Plain-language recommendation
    "confirm_command": str,               # Full CLI command: weslr spine bridge --from-artifact <id> --confirm
    "requires_confirm": True,             # Structural invariant — must always be True

    # Audit trail (informational)
    "preview_generated_at": str,          # ISO-8601 timestamp — when preview was generated
    "preview_source": "quality_feedback",  # How this preview was derived
}
```

### Fields that are intentionally absent

- `signal_id` — not assigned; no bridge event has been created
- `event_id` — no inadequacy event recorded
- `bridge_object` — no `SurfaceBridgeObject` created; this is a preview, not a bridge operation
- `auto_confirm` — always False; no automatic escalation
- `operator_triggered` — not applicable; no operator action has been taken

### Example

```python
{
    "candidate": True,
    "surface_type": "artifact_weakness",
    "spine_target": "step1_inadequacy_signal",
    "urgency": "high",
    "urgency_note": "recurring limitation",
    "confidence": 0.30,
    "why": [
        "artifact substance looks thin relative to its framing",
        "strong internal score but weak external proof"
    ],
    "recommended_action": "Run validate/use on a real artifact trial; strengthen substance before promoting",
    "confirm_command": "weslr spine bridge --from-artifact agent-2-observability_trace-1776147350 --confirm",
    "requires_confirm": True,
    "preview_generated_at": "2026-04-21T13:00:00Z",
    "preview_source": "quality_feedback"
}
```

---

## SECTION 5 — SATELLITE / ARTIFACT DETAIL SURFACE

### How bridge candidate preview appears in artifact detail views

The satellite/artifact detail surface must display `quality_feedback` (from Slice 1) and, when eligible, `bridge_candidate_preview`. The layout should make the distinction clear: quality feedback is self-assessment; the preview is an escalation suggestion requiring operator judgment.

**Proposed layout for artifact detail section:**

```
══════════════════════════════════════════════════
ARTIFACT: Observability Trace
ID: agent-2-observability_trace-1776147350
Type: tradable_component  ·  Family: observability
Created: 2026-04-13  ·  Status: prototype
══════════════════════════════════════════════════

WESLR SELF-ASSESSMENT  (quality_feedback)

Quality:    early-stage, substance still forming
Weakness:   artifact substance looks thin relative to its framing
            strong internal score but weak external proof
Next step:  run validate/use or validate/accept on a real artifact trial

Proof:      Human approvals: 0  ·  Real usage: 0  ·  Handoff accepts: 0

──────────────────────────────────────────────────
⚠️  ESCALATION CANDIDATE  (bridge_candidate_preview)

This artifact shows signs of a recurring structural weakness.
Operator review is recommended before the artifact progresses further.

  Urgency:   high (recurring limitation)
  Confidence: 0.30
  Why:       substance looks thin relative to framing
            no durable external proof yet

  If you want to escalate:
  weslr spine bridge --from-artifact agent-2-observability_trace-1776147350 --confirm

  [This is a preview only. No action has been taken.]
──────────────────────────────────────────────────

No action required — display only.
```

### What the surface must show

When `bridge_candidate_preview` is present:

- `urgency` and `urgency_note` — clearly visible, not minimized
- `why` list — the specific weakness signals that triggered eligibility
- `confirm_command` — the exact CLI command the operator would run
- `requires_confirm: True` — explicitly stated to reinforce no auto-escalation
- `preview_generated_at` — so the operator knows how fresh the preview is
- A clear visual distinction between `quality_feedback` (Slice 1) and `bridge_candidate_preview` (Slice 2)

### What the surface must NOT do

- Must not display a confirm/reject button — operator must run the CLI command themselves
- Must not show `bridge_candidate_preview` when `candidate == False` or when not eligible
- Must not minimize or hide `urgency_note`
- Must not auto-populate the urgency from anything other than the existing derivation logic
- Must not link directly to any Step 1 function

---

## SECTION 6 — GOVERNANCE BOUNDARY

This section defines the hard limit between presentation and execution.

### What is allowed in Slice 2

- Computing `bridge_candidate_preview` from existing `quality_feedback` data
- Adding `bridge_candidate_preview` to the artifact detail payload (in `build_artifact_detail_views()`)
- Displaying the preview in the satellite UI
- Showing the `confirm_command` string to the operator

### What is explicitly prohibited

**No Step 1 write at generation time.** The `bridge_candidate_preview` is computed at display time (when `build_artifact_detail_views()` is called), not at artifact creation time. No call is made to `record_inadequacy_event()`.

**No bridge preview auto-confirm.** The `requires_confirm` field is always `True`. The satellite UI never applies `--confirm` automatically. The operator must run the CLI command manually.

**No automatic CDI.** A `bridge_candidate_preview` does not trigger `cognitive_dialogue_integration.build_cdi_bundle()` or any dialogue flow.

**No proposal creation.** The preview does not create a `ChangeProposal`, `InsightProposalPayload`, or any other proposal object.

**No hidden escalation logic.** The preview is a passive data structure. It cannot route, decide, or execute anything.

**No new execution path.** The only escalation path remains `weslr spine bridge --from-artifact <id> --confirm`. The preview does not create, shorten, or parallelize that path.

---

## SECTION 7 — FORBIDDEN DRIFT

This section enumerates specific behaviors that are prohibited under this design. These are architectural constraints, not implementation notes.

### Absolute prohibitions

**1. No direct escalation from quality feedback.**
A `bridge_candidate_preview` may be present in the artifact detail payload. This does not mean the artifact is escalated. Escalation requires the operator to run the CLI command manually. The preview is a suggestion, not a trigger.

**2. No new bridge type.**
`surface_type` must be `artifact_weakness`. No new `SURFACE_TYPE` value may be introduced to accommodate quality feedback escalation. If the existing surface type is insufficient, the design is invalid and must be revised.

**3. No automatic operator-proxy confirmation.**
OC Coder may not confirm a bridge candidate preview in Slice 2. The `confirm_command` must be shown, not executed. Any implementation that surfaces a confirm button or auto-fills `--confirm` is a governance violation.

**4. No hidden score tuning.**
The eligibility rules use only existing signals from `build_artifact_explainability()`. The `internal_score`, `confidence`, or any other scoring parameter may not be adjusted specifically to make more or fewer artifacts eligible for preview. The scoring is descriptive, not constitutive.

**5. No turning generation-time evaluation into a parallel self-improvement loop.**
`quality_feedback` at generation time is observational. It does not create proposals, inadequacy events, or CDI bundles. The bridge candidate preview in Slice 2 is a display enhancement. Neither is a self-improvement mechanism on its own.

**6. No preview generation for already-resolved artifacts.**
Artifacts with `review_status` of `approved`, `export_ready`, `packed`, or `deployed` do not produce a `bridge_candidate_preview`. Artifacts that already have `bridge_confirmed` do not produce a new preview.

**7. No urgency derived from the preview itself.**
The `urgency` and `urgency_note` in the preview are computed using the existing urgency derivation logic in `surface_to_spine_bridge.py`. No new urgency computation may be introduced in `build_artifact_detail_views()` or any other display-layer function.

---

## SECTION 8 — RECOMMENDED FIRST IMPLEMENTATION

### Smallest safe first step

Slice 2 has a narrower scope than Slice 1: it is a display-layer change only. The `bridge_candidate_preview` is added to `build_artifact_detail_views()` in `sim.py` when eligibility criteria are met. No CLI changes. No bridge module changes. No new files.

**First implementation scope:**

1. **Add `build_artifact_candidate_preview()` helper in `sim.py`.**
   Pure function: takes artifact meta dict, returns `bridge_candidate_preview` dict or `None`. Uses existing `build_artifact_explainability()` and the same urgency derivation logic from `surface_to_spine_bridge.py` (duplicated by value, not by reference — no import of bridge logic into sim.py to avoid circular dependencies).
   Placement: near `build_artifact_detail_views()` in `sim.py`.

2. **Add `bridge_candidate_preview` to `build_artifact_detail_views()`.**
   After building each detail dict, call `build_artifact_candidate_preview(item)`. If it returns a non-None result, add it as `bridge_candidate_preview` in the detail dict.

3. **Display in satellite UI.**
   The HTML template in `sim.py`'s `render_dashboard()` already renders `quality_feedback`. Add a conditional section for `bridge_candidate_preview` using the layout in Section 5. This is a template addition only — the data is already in the payload from `build_artifact_detail_views()`.

4. **No CLI changes.** The `weslr spine bridge` command is unchanged. No new subcommand.

5. **No test file changes to existing tests.** Add new tests in `weslr/test_artifact_quality_feedback.py` to cover the new preview logic.

**What this slice does NOT include:**

- No changes to `surface_to_spine_bridge.py`
- No new CLI commands
- No confirm/reject UI buttons
- No operator-proxy action
- No urgency computation introduced — reuse by value from existing logic
- No `signal_id` or `event_id` assigned
- No writes to `record_inadequacy_event()`

**Validation for Slice 2:**

- `bridge_candidate_preview` is `None` for artifacts with urgency `low`
- `bridge_candidate_preview` is present for artifacts with urgency `medium` or `high` and weakness indicators
- `bridge_candidate_preview` is `None` for artifacts with `review_status` = `approved`
- `confirm_command` contains the correct artifact ID and `--confirm` flag
- `requires_confirm` is always `True`
- Satellite UI displays the preview section when present, omits it when absent
- No existing tests break

---

## SECTION 9 — STOP LINE

This document is a **design specification**. It authorizes no code changes. It creates no implementation obligation. It does not modify any existing module, schema, or behavior.

**Enforcement:**

- No changes to `surface_to_spine_bridge.py`
- No new CLI commands
- No confirm/reject UI controls in this slice
- No operator-proxy activation
- No writes to `record_inadequacy_event()`
- No new `SURFACE_TYPE` value
- No changes to `weslr/main.py`

**Next step:** Operator reviews this document. If approved, implementation of Section 8 may be authorized in a separate instruction. Slice 3 (confirm/reject UI controls) remains deferred.

---

**Document:** ARTIFACT_QUALITY_FEEDBACK_LOOP_SLICE2_V1.md  
**Authored:** 2026-04-21  
**Status:** SEALED — Operator Design Intent  
**Stop line active:** Yes  
**Depends on:** ARTIFACT_QUALITY_FEEDBACK_LOOP_V1.md (Slice 1 — implemented)
