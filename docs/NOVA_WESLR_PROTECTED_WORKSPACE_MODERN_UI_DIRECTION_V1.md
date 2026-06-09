# NOVA_WESLR_PROTECTED_WORKSPACE_MODERN_UI_DIRECTION_V1.md

**Date:** 2026-06-09 21:59  
**Status:** DESIGN DISCOVERY COMPLETE ✅  
**Mode:** Documentation only — no source edits, no deploys, no behavior change  
**Scope:** Strategic design direction for the protected workspace shell (`chat.weslr.de`)

---

## 0. Important Framing

This report is a **direction document**, not a pixel-perfect spec or an implementation patch. It captures intent, structure, and visual language so that future UI work has a coherent target to converge on.

**This report does NOT copy Perplexity or Cursor.** It draws only on the modern interaction principles those products are known for, then reinterprets them through WESLR's identity:

> Continuity-first operational intelligence. Governed, traceable, operator-approved. Project-based workspace. Protected/private by default. Evidence/context aware. Artifact-oriented. Owner-controlled environment settings. German/engineering-grade trust — not magic chatbot.

WESLR is a **governed operator cockpit**, not a public AI playground.

---

## 1. Stabilize Current Source/Deployed and `/api/message`

### Status
- ✅ **Done in Step A (commit `d445bb2`):** Source reconciled with deployed. `/api/message` fetch is present in source line 487. Source and deployed are byte-identical (`cmp -s` returned `SOURCE_DEPLOYED_MATCH`).
- ✅ Pre-reconciliation backup preserved locally as `protected-preview/chat-app-shell/index.html.pre-reconcile-20260609-215300.bak`.
- ✅ `UI Preview Only` removed from source (count 0). `Backend not connected` banner still present (informational, conditional display TBD).

### Why first
- All future UI work builds on a stable baseline. Regressing `/api/message` again would break the entire protected surface.
- The reconciliation patch is the foundation; everything below assumes it.

### What's required to maintain this stability
- Do not run `git reset HEAD~n` on the repo. Use `git revert <sha>` for rollback.
- Before any re-deploy, run `cmp -s protected-preview/chat-app-shell/index.html /var/www/weslr-chat-app-shell/index.html` and refuse to proceed if they differ.
- Keep the deployed file as the source of truth for "what works"; reconcile source to deployed, not the other way.

---

## 2. Replace Bottom Buttons with Modern Action Chips

### Current problem
- 5 separate `icon-btn` controls (⚙ 📄 🔍 ⚙️ ☰) plus a Send button
- Two render as ⚙/⚙️ — easy to confuse
- 34×34 hard-bordered squares, `border-radius: 8px`
- No labels on desktop
- Wraps awkwardly on narrow widths

### Proposed change
Replace the 5-icon button row with a **horizontal action chip rail** above the composer.

**Action chip set (in priority order):**
1. **Project** — opens Project drawer
2. **Evidence** — opens Evidence drawer
3. **Artifact** — opens Artifacts drawer
4. **Settings** — opens Settings drawer
5. **Memory** — opens Memory / Continuity drawer

**Send** is a single primary button at the right of the input — not a chip.

**Visual style:**
- Pill shape, 32px tall
- 12px radius
- Icon + label on desktop; icon-only on mobile (with tooltip)
- Inactive: dark slate fill, muted text
- Active (drawer open): accent-blue border, accent-blue text
- Tap target: minimum 32×32px

**Why:**
- Action chips with labels are scannable. Icons alone require memorization.
- A consistent horizontal rail is mobile-friendly without needing a separate mobile-tabs row.
- One affordance per drawer, so closing/opening is unambiguous.

---

## 3. Rebuild Mobile Panels as Bottom Sheets

### Current problem
- The mobile `<768px` sidebar collapses to a 70px horizontal strip — project names truncate.
- The `mobile-drawer` slides in from the right and has **no explicit close button** — only outside-tap or back navigation closes it.
- The `mobile-tabs` row duplicates the icon-button navigation. Two parallel navigation systems for the same panels.
- The `right-panel` (desktop) and `mobile-drawer` (mobile) carry the same content model but are not coordinated.

### Proposed change
- On mobile, every drawer becomes a **bottom sheet** with:
  - Drag handle at top (3px-tall pill, centered)
  - Header with title + explicit × close button
  - Scrollable content area
  - Drag-down-to-dismiss gesture
- **One sheet at a time.** Opening a new one closes the previous.
- Project list becomes a **topbar selector chip** (project name + ▾) that opens a project picker sheet.
- The `mobile-tabs` row is **removed entirely** — replaced by the action chip rail (see §2).

**Visual style for bottom sheets:**
- Slides up from the bottom, max-height 85vh
- Background: `--bg-secondary` with 16px top radius
- Drag handle: 36px × 4px pill, `--text-muted` color
- Header: 48px tall, title left, × right
- Body: padded 16px
- Backdrop: `rgba(0,0,0,0.5)` over the rest of the screen

**Why:**
- Bottom sheets are a familiar pattern from iOS/Android — users expect them.
- One-sheet-at-a-time removes the "which panel am I looking at" ambiguity.
- Explicit × is mandatory; implicit dismissal is hostile.

---

## 4. Add Right-Side Inspector on Desktop

### Current problem
- The `.right-panel` is a fixed 320px column that **only renders content when a panel is active**. There is no always-visible right-side context.

### Proposed change
Introduce a **right-side inspector** on desktop (≥1024px) that is structurally separate from the action-chip drawers.

**Inspector scope (always-visible, lightweight):**
- Project continuity indicator
- Role/security chip
- Backend status chip
- Quick artifact count + most recent artifact link
- Memory / continuity chip

**Drawer scope (on-demand, opened by action chips):**
- Project details
- Evidence
- Artifacts (full list)
- Settings
- Memory

**Why the split:**
- Status, role, backend, project name are **always relevant** — they should not be hidden behind a chip.
- Drawers are for **on-demand inspection** of larger content (full evidence, full artifact list, full settings).

**Layout impact:**
- Desktop layout becomes a 3-column grid: project rail (240px) + chat (flex) + inspector (280px).
- Total fixed side width: 520px. Maintains the 800px max content width for chat.

**Why:**
- Continuous visibility of role/backend/continuity reinforces the "operator cockpit" identity.
- Decoupling inspector from drawer avoids the "where did the panel go" confusion.

---

## 5. Add Owner Settings Role-Gated Panel

### Current problem
- The Settings panel content is generic. There is no owner-only lock, no environment state, no approval gating visible.

### Proposed change
The Settings drawer surfaces only what the **current role** can actually change.

**Role hierarchy:**
- **Owner** — sees all toggles, can change environment settings, can approve writes
- **Admin** — sees most toggles, can manage projects, cannot change owner-only environment
- **Tester** — sees read-only labels + a "Test mode" indicator
- **Viewer** — read-only labels only; no toggles

**Backend contract assumed (to be confirmed with owner):**
```json
{
  "role": "owner",
  "writes_enabled": false,
  "google_auth_enabled": false
}
```

**Owner-only toggles (examples):**
- `writes_enabled` — global write permission gate
- `google_auth_enabled` — toggle Google OAuth availability
- `streaming_enabled` — enable progressive token response
- `evidence_ingestion` — enable evidence/artifact pipeline
- `command_palette_enabled` — enable ⌘K palette

**High-risk writes** (artifact creation, settings change, project mutation) require `writes_enabled: true` AND a confirmation toast.

**Visual:**
- Toggles: iOS-style switches, accent-blue when on, gray when off
- Each setting: card with title, 1-line description, switch aligned right
- Owner-only items: subtle "Owner" badge in the top-right corner of the card

**Why:**
- Role gating is non-negotiable for an "operator-approved" product.
- The current `writes_enabled: false` lock must be visibly enforced, not just configured.

---

## 6. Add Evidence/Artifact Response Cards

### Current problem
- `sendMessage()` posts to `/api/message` and renders the raw `data.response_text`. There is no structured rendering of evidence (sources) or artifacts (generated files).

### Proposed change
Each `/api/message` response renders as a **WESLR response card** with optional evidence and artifact sections.

**Response card structure:**
```
┌──────────────────────────────────────────┐
│  WESLR Response                          │ ← header
│  [evidence-chip] [evidence-chip]         │ ← optional evidence row
│                                          │
│  Response body text...                   │ ← main content
│                                          │
│  ┌────────────────────────────────┐      │
│  │  📄 artifact-name.pdf          │      │ ← optional artifact card
│  │  12 KB · generated 2m ago      │      │
│  └────────────────────────────────┘      │
│                                          │
│  Path: /api/runtime/...  ·  14:32:01     │ ← metadata footer
└──────────────────────────────────────────┘
```

**Backend contract assumed (to be confirmed with owner):**
```json
{
  "response_text": "...",
  "evidence": [
    {"id": "src_001", "label": "Source A", "path": "/api/evidence/src_001"},
    {"id": "src_002", "label": "Source B", "path": "/api/evidence/src_002"}
  ],
  "artifacts": [
    {"id": "art_001", "name": "weslr-pilot-brief.pdf", "size": 12288, "created_at": "2026-06-09T14:30:00Z", "path": "/api/artifacts/art_001"}
  ],
  "path": "/api/runtime/...",
  "stream_id": null
}
```

**Evidence chip behavior:**
- Small pill, monospace font, link-style
- Tap → Evidence drawer opens, scrolls to that source
- Hover → tooltip with full source label

**Artifact card behavior:**
- Card with file icon, name, size, "generated Xm ago"
- Tap → Artifact drawer opens, showing full preview
- Disabled state if `writes_enabled: false` and the artifact is a "write" type

**Why:**
- Evidence and artifacts are the WESLR identity. They must be first-class in the response surface.
- The current implementation throws away all the structured data and renders only `response_text`.

---

## 7. Add Command Palette / Action Menu

### Current problem
- All actions go through the action chip rail. There is no keyboard-driven quick action.
- A "command palette" pattern is a major differentiator of modern operator tools.

### Proposed change
A **command palette** is invoked by:
- ⌘K (macOS) / Ctrl+K (Windows/Linux)
- Tap on the "⌘" action chip in the rail

**Palette structure:**
```
┌──────────────────────────────────────────┐
│  🔍  Type a command or search...         │
├──────────────────────────────────────────┤
│  ↗  New project                          │
│  ⇄  Switch project                       │
│  🔍  Open evidence                       │
│  📄  Open artifacts                      │
│  ⚙  Open settings                        │
│  ⌘  Toggle streaming                     │
│  ⚠  Toggle writes (owner only)           │
└──────────────────────────────────────────┘
```

**Visual:**
- Modal overlay, centered, 560px max width
- Search field at top, autofocused
- Action list below, 6–8 actions
- Selected action highlighted with accent-blue background
- Esc closes, ↑/↓ navigates, Enter executes

**Scope for v1:**
- v1 ships a **placeholder** command palette — visually present, but only 3–4 actions are wired (Open Settings, Open Evidence, Switch Project, New Project).
- Full action coverage comes in a later phase.

**Why:**
- The placeholder establishes the affordance and the keybinding.
- A real command palette is a major differentiator but needs a stable action surface to wire against.

---

## 8. Add Streaming / Pending Response Polish

### Current problem
- The current `sendMessage()` shows a hard "Sending..." pending message and replaces it with the result. No streaming dots, no cursor, no progressive reveal.

### Proposed change
Replace the hard "Sending..." pending state with **typing dots** in an assistant bubble.

**Pending state structure:**
```
┌──────────────────────────────────────────┐
│  WESLR                                   │
│                                          │
│  ● ● ●                                   │ ← three animated dots
│                                          │
└──────────────────────────────────────────┘
```

**Animation:**
- Three dots, 6px diameter each
- Each dot fades from 0.3 to 1.0 opacity in sequence, 600ms cycle
- Subtle, non-distracting

**Streaming (when backend supports it):**
- The pending bubble transforms into a streaming assistant bubble
- Tokens append progressively as they arrive
- A blinking cursor (`|`) at the end of the last token
- When complete, the cursor disappears

**Cancel affordance:**
- A small "×" appears in the top-right of the pending/streaming bubble
- Tap to abort the fetch
- No message is sent

**Error state:**
- If `/api/message` returns an error, the pending bubble is replaced with an error card
- Error card: red left border, error icon, error message, "Retry" action

**Why:**
- Modern operator tools feel responsive. A 200ms response should not look identical to a 2s response.
- The cancel affordance is critical for a 30+ second long-running WESLR query.

---

## H. Non-Copying Boundary (Explicit)

This section is the explicit, non-copied boundary for the entire design.

### H1. Inspiration only
- Perplexity and Cursor are referenced as **inspiration for interaction patterns only**.
- No specific screen, layout, or visual treatment is being replicated.
- The goal is to **learn from the principles** (answer-centered layout, project-first, command palette, streaming feel, evidence visibility) and reapply them through WESLR's identity.

### H2. No cloned UI
- **WESLR is not Perplexity.** WESLR is a governed operator cockpit, not a public research engine. There is no "ask anything" field. There is no share button. There is no "related questions" panel.
- **WESLR is not Cursor.** WESLR is not a code editor. There is no file tree. There is no diff viewer. There is no inline-edit affordance.
- No layout, color scheme, or visual treatment is being copied.

### H3. WESLR keeps its own identity
- **Continuity-first operational intelligence** — WESLR surfaces project continuity as a first-class indicator.
- **Governed, traceable, operator-approved** — every action is gated by role; every response carries a `path` and a timestamp.
- **Project-based workspace** — projects are the navigation primitive, not chat threads.
- **Protected/private by default** — no public link generation, no share, no invite.
- **Evidence/context aware** — evidence chips are inline in the response, not a sidebar afterthought.
- **Artifact-oriented** — artifacts (generated files) are first-class cards, not download links.
- **Owner-controlled environment settings** — settings drawer is role-gated, not user-gated.
- **German/engineering-grade trust** — restrained visual language, no marketing flourishes, no magic.

### H4. No Perplexity or Cursor trademarks
- No Perplexity logomark, color, or layout treatment.
- No Cursor logomark, color, or layout treatment.
- No Perplexity or Cursor copy text.
- No reference to those products anywhere in the protected app.

### H5. Boundary enforcement
- **At implementation time:** any new component must pass a check: "Does this look like Perplexity or Cursor?" If yes, redesign.
- **At review time:** owner reviews the design and explicitly approves or rejects any element that feels borrowed.
- **Long-term:** if WESLR ever ships a public-facing surface, none of these patterns may leak into it.

---

## I. What This Report Does NOT Change

- ❌ No source code edits
- ❌ No deploys
- ❌ No nginx / auth / Cloudflare / DNS changes
- ❌ No model changes
- ❌ No Google OAuth
- ❌ No public chat / public registration
- ❌ No high-risk writes enabled
- ❌ No backend contract changes
- ❌ No removal of existing functionality (everything works, the new look layers on top)

This is a **direction document**. Phased implementation requires separate dispatches with owner approval at each phase.

---

## J. Rollback / Forward Path

If this direction is approved, the next dispatch would be **Phase 1 — Component foundation**, which is a CSS + markup refactor with **zero behavior change**. The current working `sendMessage()`, `/api/message` fetch, and all panel toggles would remain functional throughout.

If this direction is **not** approved, the working `index.html` from Step A reconciliation remains untouched and live.

---

## K. Open Questions for Owner

1. **Backend `/api/auth/me` contract:** What does the response actually contain today? The rehydration report did not see `writes_enabled` or `google_auth_enabled` fields — only `role` is referenced. Should I curl with creds to confirm?
2. **Drawer scope priority:** Is the Evidence / Artifact / Settings / Memory drawer set the right four? WESLR-specific (continuity, artifact) — should one be split into "Memory" and "Continuity"?
3. **Command palette:** Build a real one, or keep a stub for v1? Cursor's ⌘K is a major differentiator.
4. **Streaming:** Does the backend support SSE / WebSocket / chunked responses, or is the current implementation a single JSON response?
5. **Owner role-switch preview:** Some operator tools (Linear, Vercel) let the owner preview the UI "as Admin" or "as Viewer". Is that in scope?
6. **Brand mark:** The current logo is a flat "W" square. Is there a Weslr logomark I should be using instead?
7. **No emoji as action:** I am proposing to drop emojis (📄 🔍 ⚙️ ☰) from primary action affordances. Owner approval?

---

## L. Final Judgment

`nova_weslr_protected_workspace_modern_ui_direction_ready_for_owner_review`

Direction captured. No code, no deploy, no behavior change. Awaiting owner review and approval to begin Phase 1 (component foundation, CSS refactor, behavior-preserving).

---

**Report author:** Nova (Telegram dispatcher, WESLR ops context)  
**Active model during report:** `minimax-m3:cloud`  
**Owner-visible next actions:**
1. Review the direction above (sections 1–8, then boundary H)
2. Answer the open questions in section K (especially the `/api/auth/me` contract and the streaming question)
3. Approve Phase 1 as the next dispatch
4. Or amend the direction before any implementation begins
