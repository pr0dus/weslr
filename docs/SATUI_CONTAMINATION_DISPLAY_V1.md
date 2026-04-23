# SATUI CONTAMINATION DISPLAY V1
**Generated:** 2026-04-22 19:46 GMT+2
**Mode:** STRICT — design only, no code changes, no routing changes, no scoring changes, no governance changes
**Authors:** Main agent
**Sources:** docs/RUNTIME_CONTAMINATION_METADATA_V1.md, weslr/contamination_detector.py, docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md

---

## SECTION 1 — PURPOSE

### Why Contamination Metadata Should Be Visible to Operators

WESLR's operator works with continuity every day — "improve this", "explain this", "work with that artifact". When contamination occurs, the operator has a right to know that "this" resolved to something that might not belong in the current context. Without visibility, the operator cannot make informed decisions about whether to accept, redirect, or override a resolution.

Contamination is not a failure — it is a **signal**. The operator's job is to evaluate the signal and act. SatUi exists to help the operator see what is happening, not to make decisions for them.

Making contamination visible serves three goals:
1. **Operator trust** — the operator sees that WESLR knows the difference between healthy continuity and contamination
2. **Informed override** — the operator can say "actually, I meant the artifact from Session A" when contamination is flagged
3. **Pattern recognition** — over time, the operator can see when and how contamination tends to occur, and provide guidance

### Why This Must Remain Advisory Only

SatUi is a view layer — it displays signals. It does not make decisions. If contamination display becomes control logic (e.g., "hide this button when contamination risk is high"), the UI is making the same decision that runtime filtering would make: removing operator agency.

The boundary is clear: SatUi shows risk level, type, confidence, and reason. The operator decides what to do. SatUi does not block, redirect, or suppress based on contamination.

---

## SECTION 2 — CURRENT REALITY

### Where Contamination Metadata Exists Today

| Form | Location | Shape |
|---|---|---|
| Runtime | `dialogue.py:_resolve_active_artifact()` → `research_context["_contamination_metadata"]` | `_contamination_metadata: {present, risk_level, type, reason, source_signals, confidence, advisory_only}` |
| Eval artifacts | `cross_session_artifact_eval.py` → `contamination_advisory` block | `contamination_advisory: {contaminated, type, confidence, reason, source_signals}` |
| Analysis | `relevance_eval_analysis.py` → contamination section | Aggregated pattern report |

### Runtime vs Eval Artifact Forms

**Runtime form** (`_contamination_metadata`):
```json
{
  "present": true,
  "risk_level": "none|low|medium|high",
  "type": "none|cross_domain_contamination|unrelated_topic_bleed|...",
  "reason": "...",
  "source_signals": [...],
  "confidence": "low|medium|high",
  "advisory_only": true
}
```
Attached to the response dict for each resolved reference turn. Surfaces in real-time.

**Eval artifact form** (`contamination_advisory`):
```json
{
  "contaminated": true|false,
  "type": "...",
  "confidence": "...",
  "reason": "...",
  "source_signals": [...]
}
```
Written after evaluation runs. Used for post-hoc analysis, not real-time display.

### Healthy / Safe / Contaminated Examples

| Scenario | `risk_level` | `type` | `confidence` | `reason` |
|---|---|---|---|---|
| Same-domain reference turn ("explain this" → PV artifact) | `none` | `none` | `high` | no contamination signals detected |
| Safe no-artifact path (no artifact exists) | — (field absent) | — | — | not applicable |
| PV artifact resolving to unrelated "capital of France" | `high` | `cross_domain_contamination` | `high` | artifact from prior domain appears on unrelated turn |
| Artifact context present with empty message relevance | `medium` | `unrelated_topic_bleed` | `medium` | artifact context present with weak/empty message relevance |

---

## SECTION 3 — DISPLAY MODEL

### What SatUi Should Show

SatUi displays contamination metadata as an **advisory indicator panel** on reference turns. The panel is not a modal, not a confirmation dialog, not a blocking UI element. It is a visible indicator that the operator can ignore or act on.

The display model has four components:

#### 1. Risk Indicator Icon
A small, non-intrusive icon next to the resolved artifact label:
- `risk_level: none` → no indicator (nothing to show)
- `risk_level: low` → subtle neutral indicator
- `risk_level: medium` → amber/yellow indicator
- `risk_level: high` → red indicator

The icon is purely informational. It does not disable buttons or change navigation.

#### 2. Contamination Type Label
A short text label showing the contamination type:
- `none` → not displayed
- `cross_domain_contamination` → "Domain mismatch"
- `unrelated_topic_bleed` → "Topic bleed"
- `stale_context_dominance` → "Stale context"
- `wrong_active_artifact_persistence` → "Wrong artifact"

#### 3. Expandable Reason Panel
A collapsed panel that the operator can expand to read the reason:
- `reason` field shown in plain language
- Collapsed by default for `none` and `low`
- Collapsed by default for `medium` unless operator preference is set
- Visible by default for `high`

#### 4. Source Signals (Diagnostic Detail)
An optional diagnostics view:
- Listed as a short tag list: `#message_domain_mismatch #artifact_context_present`
- Shown only when the operator expands the panel
- Not shown at all for `risk_level: none`

### Display for Each State

| State | Indicator | Type Label | Reason Panel | Signal Tags |
|---|---|---|---|---|
| Healthy (`risk_level: none`) | None | None | None | None |
| Safe path (field absent) | None | None | None | None |
| Low risk | Subtle neutral | Shown | Collapsed | Hidden |
| Medium risk | Amber | Shown | Collapsed | Hidden |
| High risk | Red | Shown | Visible | Visible on expand |

### Color and Severity Semantics

| Risk Level | Color | Meaning |
|---|---|---|
| `none` | None | Continuity is clean |
| `low` | Neutral/gray | Minor signals; informational |
| `medium` | Amber/yellow | Possible contamination; review if desired |
| `high` | Red | Likely contamination; operator should review |

Color is a **signal**, not a **status**. Red does not mean "something is broken." It means "review suggested."

---

## SECTION 4 — WHEN TO SHOW IT

### Rules for Display

**Show the contamination indicator** when ALL of these are true:
1. A reference turn was processed (`artifact_lifecycle_stage == "reference"`)
2. An artifact was resolved (not safe path)
3. `risk_level` is not `none`

**Hide the contamination indicator** (field absent) when:
1. Safe no-artifact path was taken (`_no_active_artifact == True`)
2. The turn is not a reference turn
3. `risk_level: none` — no indicator needed, clean resolution

**Expand the reason panel by default** when:
- `risk_level: high`

**Never auto-expand** for `low` or `medium` risk — the operator can expand manually.

**Never show a blocking modal or confirmation dialog** for any risk level — contamination is advisory, not a gate.

### Collapse vs Visible vs Highlighted

| Condition | Display behavior |
|---|---|
| `_contamination_metadata` absent | Nothing shown |
| `risk_level: none` | Nothing shown |
| `risk_level: low` | Indicator icon only, collapsed by default |
| `risk_level: medium` | Indicator icon + type label, collapsed by default |
| `risk_level: high` | Indicator icon + type label + reason visible + signals expandable |

### SatUi Implementation Notes

- The indicator sits **adjacent to the artifact reference**, not between the message and response
- It does not interrupt the conversational flow
- It is not a toast/notification — it is persistent on the reference turn
- It persists in the conversation history for later operator review

---

## SECTION 5 — FORBIDDEN DRIFT

### F1 — No UI → Control Bridging
**Forbidden:** Connecting the contamination indicator to logic that changes behavior — hiding buttons, disabling "improve this", prompting for confirmation.

**Why:** This converts display into control, which is the same violation as runtime filtering. SatUi shows; it does not gate.

### F2 — No Auto-Suppression of Continuity
**Forbidden:** Using a `high` contamination indicator to automatically redirect "improve this" to a different artifact or safe path.

**Why:** The operator may genuinely want to use a photovoltaic artifact as a comparison for an accounting question. The system should show the risk, not make the decision.

### F3 — No Operator Panic UI for Low/No Risk
**Forbidden:** Displaying any prominent warning, modal, or confirmation dialog for `risk_level: low` or `risk_level: none`.

**Why:** Low risk and no risk are informational only. Panic UI for these cases is noise that reduces trust.

### F4 — No Hiding Contamination on Contaminated Cases
**Forbidden:** Suppressing, minimizing, or graying out the contamination indicator on `high` risk cases to avoid alarming the operator.

**Why:** Hiding contamination on contaminated cases defeats the entire purpose of visibility. The operator must be able to see contamination risk on contaminated turns.

### F5 — No Risk Level in Routing Score
**Forbidden:** Using `risk_level` or `type` as an input to any scoring, ranking, or routing algorithm in SatUi.

**Why:** The display layer does not control routing. Risk level is for operator awareness only.

### F6 — No Color Alone as Status
**Forbidden:** Using color as the sole conveyor of contamination status (e.g., red means "bad").

**Why:** Color supplements the type label and reason. An operator who is color-blind must be able to understand contamination status from text alone.

---

## SECTION 6 — RECOMMENDED FIRST IMPLEMENTATION

### Smallest Safe First Display Slice

**Display the contamination advisory panel on reference turns in SatUi when `risk_level` is `medium` or `high`.**

What to implement:
1. Add a contamination indicator component to the reference turn view in SatUi
2. Show indicator icon + type label for `medium` and `high`
3. Show reason panel by default for `high`, collapsed for `medium`
4. Show source signal tags in an expandable section, visible on expand for `high`

What NOT to implement in first slice:
- `low` risk indicator (defer to future iteration)
- Safe path indicator (field is absent — nothing to show)
- Integration with "improve this" routing (forbidden)

### Implementation Location

The display is in SatUi, which is the operator-facing UI layer. SatUi reads `_contamination_metadata` from the runtime response dict and renders the indicator panel.

SatUi is not in the WESLR workspace — this design document specifies the contract between WESLR and SatUi:

**WESLR produces:** `research_context["_contamination_metadata"]` on resolved reference turns  
**SatUi reads:** `response._contamination_metadata` and renders the advisory indicator

### SatUi ← WESLR Contract

```
SatUi receives response dict with optional _contamination_metadata field:
{
  "_contamination_metadata": {
    "present": true,
    "risk_level": "none|low|medium|high",
    "type": "...",
    "reason": "...",
    "source_signals": [...],
    "confidence": "...",
    "advisory_only": true
  }
}
```

SatUi renders advisory panel per Section 3 display model. No additional data needed from WESLR for first slice.

---

## SECTION 7 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document defines how SatUi should display contamination metadata:
- Advisory panel adjacent to resolved artifact on reference turns
- Risk indicator icon + type label + reason panel + signal tags
- Expanded by default only for `high` risk
- Never blocking, never auto-suppressing, never hidden on contaminated cases
- Color as supplement to text, not substitute for text

### Document Completeness

| Section | Status |
|---|---|
| 1. Purpose | ✅ Complete |
| 2. Current Reality | ✅ Complete |
| 3. Display Model | ✅ Complete |
| 4. When to Show It | ✅ Complete |
| 5. Forbidden Drift | ✅ Complete |
| 6. Recommended First Implementation | ✅ Complete |
| 7. Stop Line | ✅ Complete |

---

*SATUI_CONTAMINATION_DISPLAY_V1 — Design Specification*
*Design only. No code. No routing changes. No scoring changes. No governance changes.*
