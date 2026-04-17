# UI_SATELLITE_STANDARD_V1.md
## WESLR Satellite UI — Authoritative UX Contract

> **Mandatory reading before any Satellite UI work.**
> This file is the single source of truth for what the Satellite UI is, who it serves, and what each section means.
> Drift from this contract requires explicit operator approval.

---

## 1. Purpose

The Satellite UI is WESLR's lightweight operator glanceable surface — a read-heavy, low-noise interface that gives humans a calm, consistent view of WESLR's state without requiring them to interpret raw logs or infrastructure.

It is not a dashboard. It is not a control panel. It is a **situational awareness view** for humans who need to know what WESLR is doing and how WESLR is doing it.

Key constraints:
- No configuration changes from this UI
- No direct command execution
- No raw JSON or technical dumps visible by default
- Designed for quick check-ins, not deep investigation

---

## 2. Roles Served

### Observer
A human who wants a passive, honest read on WESLR's current state. An observer checks in, sees if something needs attention, and moves on. They do not need to act — they need to **know**.

### Operator
A human who is actively responsible for WESLR's operational health. An operator uses the Satellite UI to confirm system state, read governance signals, and use Actions (primarily feedback) to communicate back. They do not use this UI to configure WESLR — they use it to **maintain awareness and communicate intent**.

Both roles share the same interface. The design assumes the observer is also the operator — no role switching is exposed in the UI.

---

## 3. Canonical Section Order

The five sections appear in this exact order, always:

| Order | Section | Tab Label |
|-------|---------|-----------|
| 1 | Situation | Situation |
| 2 | Activity | Activity |
| 3 | Evaluation | Evaluation |
| 4 | Actions | Actions |
| 5 | Charter | Charter |

This order is intentional: **what is happening → what WESLR thinks about it → what the human can do → what WESLR stands for**. Changing the order requires a design review and operator approval.

---

## 4. Section Definitions

### 4.1 Situation

**What it is:** A direct, unfiltered read on WESLR's current health and operational state.

**What belongs there:**
- System healthy/degraded status
- Uptime
- Any active alerts or error states
- Basic runtime health from `/api/health`

**What must not be there:**
- Interpretation or judgment calls
- Governance quality scores
- Activity history
- Action prompts or CTAs

**Purpose:** Answers *"what is happening right now?"* — purely factual, not interpretive.

---

### 4.2 Activity

**What it is:** A compact log of recent events in WESLR's world.

**What belongs there:**
- Recent timeline events (last 5–10)
- Timestamps and short event descriptions
- Clean, scannable list format

**What must not be there:**
- Current health state (→ Situation)
- Self-assessment verdicts (→ Evaluation)
- Feedback forms or device lists (→ Actions)

**Purpose:** Answers *"what has WESLR observed or done recently?"*

---

### 4.3 Evaluation

**What it is:** WESLR's own interpretation of its current state — how it reads the situation.

**What belongs there:**
- Governance quality signals
- Risk posture summary
- Self-assessment verdict in plain English
- Strengths and weaknesses at a glance

**What must not be there:**
- Raw health metrics (→ Situation)
- Event history (→ Activity)
- Feedback forms (→ Actions)

**Purpose:** Answers *"how does WESLR interpret what is happening?"* — this is the judgment layer, not the fact layer.

---

### 4.4 Actions

**What it is:** A bounded area where the human can communicate intent back to WESLR and see what capabilities and devices are available.

**What belongs there:**
- Feedback submission form (wired to `POST /api/feedback`)
- Devices list (from `/api/devices`)
- Capabilities list (from `/api/capabilities`)

**What must not be there:**
- Detailed governance data (→ Evaluation or Charter)
- Raw health or event data (→ Situation / Activity)
- Configuration controls

**Purpose:** Answers *"what can I (the human) do right now, and what does WESLR have access to?"* — communication outward, inventory inward.

---

### 4.5 Charter

**What it is:** WESLR's foundational operating principles rendered in a human-readable form.

**What belongs there:**
- Guiding principles (short list)
- Trust hierarchy (who ranks where)
- What WESLR watches for (poisoning defense signals)
- Any active trust or poisoning defense signals

**What must not be there:**
- Real-time operational state (→ Situation)
- Event history (→ Activity)
- Feedback or action forms (→ Actions)

**Purpose:** Answers *"what does WESLR stand for, and what does it protect against?"* — static-ish reference, refreshed on load.

---

## 5. Language and Tone Rules

- **Active voice only.** No passive constructions.
- **Plain English.** No jargon visible to the human. Internal terms (trust_level, governance_quality) are translated to human phrases.
- **No uncertainty-theater.** If WESLR doesn't know something, it says "unavailable" — not "possibly" or "maybe".
- **Short sentences.** Target 10–15 words per sentence in visible text.
- **Verdict-first.** Evaluation section leads with the verdict ("Everything looks normal" / "Something needs attention"), not the data that led to it.
- **Empty states are calm.** "No recent activity yet." is better than "No data available." — acknowledges the state without alarm.
- **Feedback confirmation is warm.** "Feedback sent — thank you." not "Submitted."

---

## 6. Visual Rules

- **One tab visible at a time.** No split view.
- **No scrollable tab content.** All tab content fits within a single viewport height. If content grows, it truncates gracefully with a note.
- **No spinners after initial load.** Loading states are plain text placeholders that update once. No looping animations.
- **No raw JS, no raw JSON visible.** Debug panel is collapsed by default.
- **Color usage:**
  - `#6ee7b7` (green) — accent for labels, active states, positive signals
  - `#9aa6b2` (muted grey) — secondary text, labels, descriptions
  - `#e7ecf3` (near-white) — primary readable text
  - `#171b22` (dark card) — card backgrounds
  - `#0f1115` (dark background) — page background
- **No gradients, no shadows, no decorative elements.**
- **Font:** System UI (no web fonts loaded).
- **Mobile-first:** nav buttons wrap at 400px; content remains readable without zoom.
- **Refresh persistence:** active tab is saved to `sessionStorage` and restored on page reload.

---

## 7. Anti-Drift / Regression Rules

### Mandatory Before Any Satellite UI Work
1. Read this file.
2. Confirm the change against each section definition.
3. Run a visual check across all 5 tabs after the change.

### Prohibited Without Explicit Approval
- Adding a 6th tab or reordering existing tabs
- Mixing content from one section into another (e.g., governance data in Situation)
- Showing raw JSON or technical dumps in any section
- Adding spinners or looping loading states after tab content loads
- Using the Satellite UI for control or configuration actions
- Removing the tab persistence feature

### Validation Checklist Before Commit
- [ ] All 5 tabs still navigate correctly
- [ ] No visible spinners after content load
- [ ] Empty states display as calm text, not blank space
- [ ] Refresh returns to the previously active tab
- [ ] No raw JS or JSON visible in any section
- [ ] Mobile layout doesn't overflow at 400px width
- [ ] All endpoints are existing stable endpoints (no new backend required)
- [ ] One script block only
- [ ] No regressions in other sections

### What Does Not Count as a Regression
- Adding new endpoint wiring to Actions (devices, capabilities, feedback)
- Polishing empty state styling
- Improving mobile layout
- Refactoring Charter section headings and label formatting
- Compressing Charter content for readability

---

## 8. Critical Distinction: Situation vs Evaluation

This distinction is the most important architectural rule in this contract.

| | Situation | Evaluation |
|--|-----------|------------|
| **Question answered** | What is happening? | What does WESLR think about it? |
| **Source** | Runtime health (facts) | Self-assessment + governance (judgment) |
| **Tone** | Factual, neutral | Interpretive, plain-English verdict |
| **Updates** | Fast, health-level | Slower, reflects accumulated state |
| **Example** | "System: Healthy, Uptime: 3h" | "Everything looks normal." or "1 risk detected." |

**These two sections must never be merged.** Situation is the camera. Evaluation is the editorial. They are different layers and must remain separate.

---

*Version 1 — sealed after Satellite UI recovery (2026-04-18).*
*Next review: before any Section 3 or Section 4 expansion work.*
